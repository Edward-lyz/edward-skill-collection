"""Bounded local process execution helpers.

The runtime invokes trusted local executables such as `nsys`. Keep subprocess
behavior in one place so every caller gets the same timeout cleanup: no shell,
captured output, and process-group termination when a command times out.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from subprocess import PIPE, CompletedProcess, Popen, TimeoutExpired
from typing import Any, TextIO


@contextmanager
def stderr_progress_heartbeat(
    label: str,
    *,
    interval_s: float,
    stream: TextIO | None = None,
    progress: Callable[[], int | None] | None = None,
) -> Iterator[None]:
    """Emit a periodic "still working" line to stderr for a slow local step.

    The first line is written only after ``interval_s`` elapses, so fast steps
    stay silent. A non-positive ``interval_s`` disables the heartbeat entirely.
    """

    if interval_s <= 0:
        yield
        return

    out = stream if stream is not None else sys.stderr
    stop = threading.Event()
    start = time.monotonic()
    emitted = threading.Event()

    def _beat() -> None:
        while not stop.wait(interval_s):
            elapsed = int(time.monotonic() - start)
            try:
                print(
                    f"[nsys-agent] {label} still running ({elapsed}s elapsed{_progress_suffix(progress)});",
                    file=out,
                    flush=True,
                )
            except (OSError, ValueError):
                return
            emitted.set()

    thread = threading.Thread(target=_beat, name="nsys-agent-progress", daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1.0)
        if emitted.is_set():
            elapsed = int(time.monotonic() - start)
            with suppress(OSError, ValueError):
                print(f"[nsys-agent] {label} finished ({elapsed}s).", file=out, flush=True)


def _progress_suffix(progress: Callable[[], int | None] | None) -> str:
    if progress is None:
        return ""
    try:
        pct = progress()
    except Exception:  # noqa: BLE001 - a progress probe must never break the heartbeat
        return ""
    return f", {pct}% loaded" if pct is not None else ""


def run_bounded_process(
    argv: Sequence[str | os.PathLike[str]],
    *,
    timeout_s: float,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    stderr_tap: Callable[[str], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a local command with robust timeout cleanup.

    `subprocess.run(..., timeout=...)` kills only the direct child on timeout.
    `nsys recipe` and export flows can spawn helpers, so use a process group on
    POSIX and terminate the whole group before escalating to kill.
    """

    command = [os.fspath(arg) for arg in argv]
    popen_kwargs: dict[str, object] = {
        "cwd": os.fspath(cwd) if cwd is not None else None,
        "env": dict(env) if env is not None else None,
        # A tap needs bytes off the pipe as they arrive; the buffered text
        # ``communicate`` path cannot surface progress before the process exits.
        "text": stderr_tap is None,
        "stdout": PIPE,
        "stderr": PIPE,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if creationflags:
            popen_kwargs["creationflags"] = creationflags

    # Local process boundary: argv is caller-validated, shell is never used,
    # output is captured, and timeouts terminate the process group below.
    proc = Popen(command, **popen_kwargs)  # noqa: S603  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    if stderr_tap is None:
        return _communicate_bounded(proc, command, timeout_s)
    return _stream_bounded(proc, command, timeout_s, stderr_tap)


def _communicate_bounded(
    proc: Popen[str], command: list[str], timeout_s: float
) -> subprocess.CompletedProcess[str]:
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except TimeoutExpired as exc:
        _terminate_process_tree(proc)
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except TimeoutExpired:
            _kill_process_tree(proc)
            stdout, stderr = proc.communicate()
        exc.output = stdout
        exc.stderr = stderr
        raise
    return CompletedProcess(command, proc.returncode, stdout, stderr)  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit


def _stream_bounded(
    proc: Popen[bytes],
    command: list[str],
    timeout_s: float,
    stderr_tap: Callable[[str], None],
) -> subprocess.CompletedProcess[str]:
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    readers = [
        threading.Thread(target=_pump_stream, args=(proc.stdout, stdout_chunks, None), daemon=True),
        threading.Thread(
            target=_pump_stream, args=(proc.stderr, stderr_chunks, stderr_tap), daemon=True
        ),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout_s)
    except TimeoutExpired:
        timed_out = True
        _terminate_process_tree(proc)
        try:
            proc.wait(timeout=2)
        except TimeoutExpired:
            _kill_process_tree(proc)
            proc.wait()
    for reader in readers:
        reader.join(timeout=2)
    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    if timed_out:
        raise TimeoutExpired(command, timeout_s, output=stdout, stderr=stderr)
    return CompletedProcess(command, proc.returncode, stdout, stderr)  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit


def _pump_stream(stream: Any, chunks: list[str], tap: Callable[[str], None] | None) -> None:
    """Drain a subprocess pipe into ``chunks``, forwarding live text to ``tap``."""

    if stream is None:
        return
    fd = stream.fileno()
    while True:
        try:
            data = os.read(fd, 65536)
        except OSError:
            break
        if not data:
            break
        text = data.decode("utf-8", errors="replace")
        chunks.append(text)
        if tap is not None:
            with suppress(Exception):  # noqa: BLE001 - a progress tap must never break the run
                tap(text)


def _terminate_process_tree(proc: Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    proc.terminate()


def _kill_process_tree(proc: Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    proc.kill()
