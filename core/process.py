from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


def pid_file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def read_pid(path: Path) -> int | None:
    if not pid_file_exists(path):
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def write_pid(path: Path, pid: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(pid), encoding="utf-8")


def clear_pid(path: Path) -> None:
    path.unlink(missing_ok=True)


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False

    exit_code = ctypes.c_ulong()
    try:
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def stop_process_tree(pid: int) -> bool:
    if not is_pid_running(pid):
        return False
    subprocess.run(
        ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return not is_pid_running(pid)


def listening_pid(port: int) -> int | None:
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "
                "| Select-Object -First 1 -ExpandProperty OwningProcess"
            ),
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    value = completed.stdout.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def process_name(pid: int) -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName"],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return completed.stdout.strip()
