"""Filesystem helpers for report caches and safe report discovery."""

from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager, suppress
from pathlib import Path

from ..path_utils import is_relative_to
from .types import ReportError


@contextmanager
def file_lock(path: Path, *, timeout_s: float):
    deadline = time.monotonic() + timeout_s
    fd: int | None = None
    stale_after_s = max(60.0, min(timeout_s, 600.0))
    while fd is None:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            if _break_stale_lock(path, stale_after_s=stale_after_s):
                continue
            if time.monotonic() > deadline:
                raise ReportError(f"timed out waiting for report export lock: {path.name}") from exc
            # Polling is deliberate here: this is a tiny cross-process cache
            # lock with no extra dependency and a strict deadline above.
            time.sleep(0.1)  # nosemgrep
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        with suppress(FileNotFoundError):
            path.unlink()


def _break_stale_lock(path: Path, *, stale_after_s: float) -> bool:
    """Remove a lock left behind by a dead process."""

    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        age_s = max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return False
    pid = int(text) if text.isdigit() else None
    if pid is not None and _pid_is_alive(pid):
        return False
    if pid is None and age_s < stale_after_s:
        return False
    with suppress(FileNotFoundError):
        path.unlink()
        return True
    return False


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        return _windows_pid_is_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _windows_pid_is_alive(pid: int) -> bool:
    """Report whether ``pid`` is running on Windows without signalling it.

    ``os.kill(pid, 0)`` cannot be reused here: on Windows signal ``0`` is not the
    POSIX "does this process exist" no-op but maps to ``TerminateProcess``, so it
    would kill a live process. It also raises a bare ``OSError`` (WinError 87,
    ERROR_INVALID_PARAMETER) for an unknown pid rather than ``ProcessLookupError``,
    which the POSIX branch does not catch. Probe with a read-only process handle
    instead: opening one succeeds only for a live process, access-denied means the
    process exists but belongs to someone else, and everything else means it is gone.
    """

    import ctypes
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    error_access_denied = 5
    still_active = 259

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)

    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return ctypes.get_last_error() == error_access_denied
    try:
        exit_code = wintypes.DWORD()
        if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return exit_code.value == still_active
        return True
    finally:
        kernel32.CloseHandle(handle)


def safe_child_files(directory: Path, pattern: str) -> list[Path]:
    """Return direct report/export files without following symlinks outside the directory."""

    root = directory.resolve()
    files: list[Path] = []
    for path in sorted(root.glob(pattern)):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if is_relative_to(resolved, root):
            files.append(resolved)
    return files
