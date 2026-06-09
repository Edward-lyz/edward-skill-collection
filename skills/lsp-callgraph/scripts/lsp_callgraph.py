#!/usr/bin/env python3
"""Generate a bounded LSP call hierarchy graph as Crabviz-compatible HTML."""

import argparse
import json
import pathlib
import shlex
import subprocess
import sys
import threading
import time
from collections import deque
from typing import Any
from urllib.parse import unquote, urlparse

DEFAULT_EXCLUDES = (
    "/.git/",
    "/.venv/",
    "/venv/",
    "/site-packages/",
    "/node_modules/",
    "/third-party/",
    "/3rdparty/",
    "/build/",
    "/dist/",
    "/docs/",
    "/test/",
    "/tests/",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=pathlib.Path)
    parser.add_argument("--seed-file", required=True, type=pathlib.Path)
    parser.add_argument("--seed-line", required=True, type=int, help="1-based line number")
    parser.add_argument("--seed-character", required=True, type=int, help="0-based character offset")
    parser.add_argument("--language-id", required=True, help="LSP languageId, e.g. python")
    parser.add_argument("--language-name", required=True, help="Crabviz language label, e.g. Python")
    parser.add_argument("--lsp-command", required=True, help="stdio LSP command")
    parser.add_argument(
        "--direction",
        choices=("outgoing", "incoming", "both"),
        default="outgoing",
    )
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-nodes", type=int, default=80)
    parser.add_argument("--startup-wait", type=float, default=2.0)
    parser.add_argument("--exclude-substring", action="append", default=[])
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="HTML output path. Defaults to /tmp/lsp-callgraph/<repo>-<seed>-<line>-<character>.html",
    )
    return parser.parse_args()


def uri_to_path(uri: str) -> str:
    parsed_uri = urlparse(uri)
    return unquote(parsed_uri.path)


def item_key(call_item: dict[str, Any]) -> str:
    path = uri_to_path(call_item["uri"])
    start = call_item["selectionRange"]["start"]
    return f'{path}:{start["line"]}:{start["character"]}'


def vscode_symbol_kind(lsp_symbol_kind: int) -> int:
    return max(lsp_symbol_kind - 1, 0)


def normalize_symbol(symbol: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": symbol["name"],
        "kind": vscode_symbol_kind(symbol["kind"]),
        "range": symbol["range"],
        "selectionRange": symbol["selectionRange"],
        "children": [normalize_symbol(child) for child in symbol.get("children", [])],
    }


def normalize_call_item(call_item: dict[str, Any]) -> dict[str, Any]:
    normalized_item = dict(call_item)
    normalized_item["uri"] = {"path": uri_to_path(call_item["uri"])}
    normalized_item["kind"] = vscode_symbol_kind(call_item["kind"])
    return normalized_item


def normalize_outgoing_call(call: dict[str, Any]) -> dict[str, Any]:
    return {
        "to": normalize_call_item(call["to"]),
        "fromRanges": call.get("fromRanges", []),
    }


def normalize_incoming_call(call: dict[str, Any]) -> dict[str, Any]:
    return {
        "from": normalize_call_item(call["from"]),
        "fromRanges": call.get("fromRanges", []),
    }


class LspClient:
    def __init__(self, command: list[str], root: pathlib.Path, language_id: str) -> None:
        self.root = root
        self.language_id = language_id
        self.next_request_id = 1
        self.responses: dict[int, dict[str, Any]] = {}
        self.opened_uris: set[str] = set()
        self.reader_error = None
        self.is_closing = False
        self.process = subprocess.Popen(
            command,
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        self.reader_thread = threading.Thread(target=self.read_messages, daemon=True)
        self.reader_thread.start()

    def read_lsp_message(self) -> dict[str, Any]:
        if self.process.stdout is None:
            raise RuntimeError("LSP stdout is not available")

        headers: dict[str, str] = {}
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("LSP server closed stdout")
            if line == b"\r\n":
                break
            key, value = line.decode("ascii").split(":", 1)
            headers[key.lower()] = value.strip()

        content_length = headers.get("content-length")
        if content_length is None:
            raise RuntimeError("LSP response missing Content-Length")
        body = self.process.stdout.read(int(content_length))
        return json.loads(body)

    def read_messages(self) -> None:
        while True:
            try:
                message = self.read_lsp_message()
            except RuntimeError as exc:
                if not self.is_closing:
                    self.reader_error = exc
                return
            request_id = message.get("id")
            if request_id is not None:
                self.responses[int(request_id)] = message

    def send(self, payload: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise RuntimeError("LSP stdin is not available")
        raw_payload = json.dumps(payload).encode("utf-8")
        header = b"Content-Length: " + str(len(raw_payload)).encode("ascii") + b"\r\n\r\n"
        self.process.stdin.write(header + raw_payload)
        self.process.stdin.flush()

    def request(self, method: str, params: Any) -> Any:
        request_id = self.next_request_id
        self.next_request_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.reader_error is not None:
                raise self.reader_error
            response = self.responses.pop(request_id, None)
            if response is None:
                time.sleep(0.02)
                continue
            if "error" in response:
                raise RuntimeError(f"{method} failed: {response['error']}")
            return response.get("result")
        raise TimeoutError(f"LSP request timed out: {method}")

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self.send({"jsonrpc": "2.0", "method": method, "params": params})

    def initialize(self) -> None:
        root_uri = self.root.as_uri()
        self.request(
            "initialize",
            {
                "processId": None,
                "rootUri": root_uri,
                "workspaceFolders": [{"uri": root_uri, "name": self.root.name}],
                "capabilities": {
                    "textDocument": {
                        "callHierarchy": {"dynamicRegistration": False},
                        "documentSymbol": {
                            "dynamicRegistration": False,
                            "hierarchicalDocumentSymbolSupport": True,
                        },
                    },
                    "workspace": {"workspaceFolders": True},
                },
            },
        )
        self.notify("initialized", {})

    def open_file(self, uri: str) -> None:
        if uri in self.opened_uris:
            return
        path = pathlib.Path(uri_to_path(uri))
        self.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": self.language_id,
                    "version": 1,
                    "text": path.read_text(encoding="utf-8"),
                }
            },
        )
        self.opened_uris.add(uri)

    def close(self) -> None:
        self.request("shutdown", None)
        self.is_closing = True
        self.notify("exit", {})
        self.process.kill()

    def kill(self) -> None:
        self.is_closing = True
        self.process.kill()


def path_is_in_scope(path: str, root: pathlib.Path, exclude_substrings: tuple[str, ...]) -> bool:
    root_path = str(root)
    if not path.startswith(root_path):
        return False
    return not any(exclude_substring in path for exclude_substring in exclude_substrings)


def collect_callgraph(
    client: LspClient,
    seed_item: dict[str, Any],
    root: pathlib.Path,
    direction: str,
    depth_limit: int,
    max_nodes: int,
    exclude_substrings: tuple[str, ...],
) -> dict[str, Any]:
    queue: deque[tuple[dict[str, Any], int]] = deque([(seed_item, 0)])
    seen_keys: set[str] = set()
    involved_uris: set[str] = {seed_item["uri"]}
    outgoing_by_source: dict[str, list[dict[str, Any]]] = {}
    incoming_by_target: dict[str, list[dict[str, Any]]] = {}

    while queue and len(seen_keys) < max_nodes:
        current_item, current_depth = queue.popleft()
        current_key = item_key(current_item)
        if current_key in seen_keys:
            continue
        seen_keys.add(current_key)
        involved_uris.add(current_item["uri"])
        if current_depth >= depth_limit:
            continue

        if direction in ("outgoing", "both"):
            outgoing_calls = client.request("callHierarchy/outgoingCalls", {"item": current_item}) or []
            scoped_outgoing_calls = []
            for call in outgoing_calls:
                target_path = uri_to_path(call["to"]["uri"])
                if not path_is_in_scope(target_path, root, exclude_substrings):
                    continue
                scoped_outgoing_calls.append(call)
                involved_uris.add(call["to"]["uri"])
                target_key = item_key(call["to"])
                if target_key not in seen_keys and len(seen_keys) + len(queue) < max_nodes:
                    queue.append((call["to"], current_depth + 1))
            outgoing_by_source[current_key] = scoped_outgoing_calls

        if direction in ("incoming", "both"):
            incoming_calls = client.request("callHierarchy/incomingCalls", {"item": current_item}) or []
            scoped_incoming_calls = []
            for call in incoming_calls:
                source_path = uri_to_path(call["from"]["uri"])
                if not path_is_in_scope(source_path, root, exclude_substrings):
                    continue
                scoped_incoming_calls.append(call)
                involved_uris.add(call["from"]["uri"])
                source_key = item_key(call["from"])
                if source_key not in seen_keys and len(seen_keys) + len(queue) < max_nodes:
                    queue.append((call["from"], current_depth + 1))
            incoming_by_target[current_key] = scoped_incoming_calls

    return {
        "seen_keys": seen_keys,
        "involved_uris": involved_uris,
        "outgoing_by_source": outgoing_by_source,
        "incoming_by_target": incoming_by_target,
    }


def collect_symbols(client: LspClient, involved_uris: set[str]) -> dict[str, list[dict[str, Any]]]:
    symbols_by_file: dict[str, list[dict[str, Any]]] = {}
    for uri in sorted(involved_uris):
        client.open_file(uri)
        symbols = client.request("textDocument/documentSymbol", {"textDocument": {"uri": uri}})
        if symbols is None:
            raise RuntimeError(f"documentSymbol returned null for {uri}")
        symbols_by_file[uri_to_path(uri)] = [normalize_symbol(symbol) for symbol in symbols]
    return symbols_by_file


def render_html(payload_path: pathlib.Path, output_path: pathlib.Path) -> None:
    script_path = pathlib.Path(__file__).resolve().parent / "render_crabviz_html.mjs"
    subprocess.run(
        ["node", str(script_path), str(payload_path), str(output_path)],
        check=True,
    )


def main() -> int:
    args = parse_args()
    if args.seed_line < 1:
        raise ValueError("--seed-line must be >= 1")
    if args.seed_character < 0:
        raise ValueError("--seed-character must be >= 0")
    if args.depth < 0:
        raise ValueError("--depth must be >= 0")
    if args.max_nodes < 1:
        raise ValueError("--max-nodes must be >= 1")

    root = args.root.resolve()
    seed_file = args.seed_file if args.seed_file.is_absolute() else root / args.seed_file
    seed_file = seed_file.resolve()
    output_path = args.output.resolve() if args.output else pathlib.Path(
        "/tmp/lsp-callgraph",
        f"{root.name}-{seed_file.stem}-{args.seed_line}-{args.seed_character}.html",
    )
    payload_path = output_path.with_suffix(".json")
    exclude_substrings = tuple(DEFAULT_EXCLUDES) + tuple(args.exclude_substring)
    lsp_command = shlex.split(args.lsp_command)
    if not lsp_command:
        raise ValueError("--lsp-command must not be empty")

    client = LspClient(lsp_command, root, args.language_id)
    server_initialized = False
    try:
        client.initialize()
        server_initialized = True
        seed_uri = seed_file.as_uri()
        client.open_file(seed_uri)
        if args.startup_wait > 0:
            time.sleep(args.startup_wait)

        seed_items = client.request(
            "textDocument/prepareCallHierarchy",
            {
                "textDocument": {"uri": seed_uri},
                "position": {
                    "line": args.seed_line - 1,
                    "character": args.seed_character,
                },
            },
        )
        if not seed_items:
            raise RuntimeError("LSP returned no call hierarchy item for seed position")

        callgraph = collect_callgraph(
            client,
            seed_items[0],
            root,
            args.direction,
            args.depth,
            args.max_nodes,
            exclude_substrings,
        )
        symbols_by_file = collect_symbols(client, callgraph["involved_uris"])
    finally:
        if server_initialized:
            client.close()
        else:
            client.kill()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "root": str(root),
        "seed_label": seed_items[0]["name"],
        "language_name": args.language_name,
        "direction": args.direction,
        "depth": args.depth,
        "max_nodes": args.max_nodes,
        "nodes": len(callgraph["seen_keys"]),
        "edges": sum(len(calls) for calls in callgraph["outgoing_by_source"].values())
        + sum(len(calls) for calls in callgraph["incoming_by_target"].values()),
        "files": symbols_by_file,
        "outgoing": {
            key: [normalize_outgoing_call(call) for call in calls]
            for key, calls in callgraph["outgoing_by_source"].items()
        },
        "incoming": {
            key: [normalize_incoming_call(call) for call in calls]
            for key, calls in callgraph["incoming_by_target"].items()
        },
    }
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    render_html(payload_path, output_path)
    print(
        json.dumps(
            {
                "html": str(output_path),
                "payload": str(payload_path),
                "nodes": payload["nodes"],
                "edges": payload["edges"],
                "files": len(payload["files"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
