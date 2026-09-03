"""Compute *theoretical* per-tensor weight sizes from a safetensors checkpoint.

Key fact: `model.safetensors.index.json` only maps tensor-name -> shard file and
records a `total_size`; it does NOT contain shape/dtype. Those live in each
`.safetensors` file header (first 8 bytes = little-endian uint64 header length,
followed by that many bytes of JSON; every tensor entry has `dtype`, `shape`
and `data_offsets:[begin,end]`). The exact on-disk byte size is `end - begin`.

To honour "do not download the weights", remote HuggingFace repos are read with
HTTP Range requests: we fetch only the 8-byte length prefix and then the header
JSON (tens to hundreds of KB per shard), never the tensor bodies.
"""

import json
import os
import struct
from typing import Dict, List, Optional

from module_taxonomy import TensorInfo

# safetensors dtype -> bytes-per-element (for numel sanity checks / reporting).
DTYPE_ITEMSIZE = {
    "F64": 8, "I64": 8, "U64": 8,
    "F32": 4, "I32": 4, "U32": 4,
    "F16": 2, "BF16": 2, "I16": 2, "U16": 2,
    "F8_E4M3": 1, "F8_E5M2": 1, "I8": 1, "U8": 1, "BOOL": 1,
}

HF_DEFAULT_ENDPOINT = "https://huggingface.co"


def _read_local_header(path: str) -> dict:
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n))


def _read_remote_header(url: str, session, headers: dict) -> dict:
    # 1) length prefix
    r = session.get(url, headers={**headers, "Range": "bytes=0-7"}, timeout=30)
    r.raise_for_status()
    n = struct.unpack("<Q", r.content[:8])[0]
    # 2) header json
    r = session.get(
        url, headers={**headers, "Range": f"bytes=8-{8 + n - 1}"}, timeout=60
    )
    r.raise_for_status()
    return json.loads(r.content[:n])


def _header_to_tensors(header: dict) -> List[TensorInfo]:
    out = []
    for name, meta in header.items():
        if name == "__metadata__":
            continue
        begin, end = meta["data_offsets"]
        out.append(
            TensorInfo(
                name=name,
                shape=list(meta.get("shape", [])),
                dtype=meta.get("dtype", "?"),
                nbytes=int(end) - int(begin),
            )
        )
    return out


def _resolve_repo(hf: str) -> Optional[str]:
    """Turn a repo id / hf.co URL into a resolve base, or None if it's a path."""
    if os.path.isdir(hf):
        return None
    if hf.startswith("http://") or hf.startswith("https://"):
        # already a repo URL; strip any /resolve/... tail to a base
        return hf.rstrip("/")
    return None  # bare repo id handled by caller with endpoint


def load_theoretical_tensors(
    hf: str,
    rev: str = "main",
    endpoint: Optional[str] = None,
    token: Optional[str] = None,
) -> List[TensorInfo]:
    """Return all weight tensors with theoretical byte sizes.

    `hf` may be a local directory, a full hf.co URL, or a bare `org/name` repo id.
    """
    endpoint = endpoint or os.environ.get("HF_ENDPOINT", HF_DEFAULT_ENDPOINT)
    token = token or os.environ.get("HF_TOKEN")

    if os.path.isdir(hf):
        return _load_local(hf)
    return _load_remote(hf, rev, endpoint, token)


def _load_local(root: str) -> List[TensorInfo]:
    index_path = os.path.join(root, "model.safetensors.index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            shards = sorted(set(json.load(f)["weight_map"].values()))
    else:
        single = os.path.join(root, "model.safetensors")
        if not os.path.exists(single):
            raise FileNotFoundError(
                f"no model.safetensors(.index.json) under {root}"
            )
        shards = ["model.safetensors"]
    tensors: List[TensorInfo] = []
    for s in shards:
        tensors.extend(_header_to_tensors(_read_local_header(os.path.join(root, s))))
    return tensors


def _load_remote(
    repo_or_url: str, rev: str, endpoint: str, token: Optional[str]
) -> List[TensorInfo]:
    import requests  # local import so local-dir usage needs no dependency

    if repo_or_url.startswith("http"):
        base = repo_or_url.split("/resolve/")[0].rstrip("/")
    else:
        base = f"{endpoint.rstrip('/')}/{repo_or_url.strip('/')}"
    resolve = f"{base}/resolve/{rev}"

    session = requests.Session()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    idx_url = f"{resolve}/model.safetensors.index.json"
    r = session.get(idx_url, headers=headers, timeout=30)
    if r.status_code == 200:
        shards = sorted(set(r.json()["weight_map"].values()))
    else:
        shards = ["model.safetensors"]

    tensors: List[TensorInfo] = []
    for s in shards:
        url = f"{resolve}/{s}"
        tensors.extend(_header_to_tensors(_read_remote_header(url, session, headers)))
    return tensors


def format_bytes(n: int) -> str:
    gb = n / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.3f} GB"
    return f"{n / (1024 ** 2):.3f} MB"
