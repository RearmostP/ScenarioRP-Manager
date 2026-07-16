from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QProcess, QObject

from core.config import AppConfig
from core.paths import AppPaths
from core.process import clear_pid, is_pid_running, listening_pid, process_name, read_pid, stop_process_tree, write_pid
from models.process_status import ProcessStatus


class FXServerService:
    def __init__(self, config: AppConfig, paths: AppPaths) -> None:
        self.config = config
        self.paths = paths
        self.pid_file = self.paths.manager_dir / "state" / "fxserver.pid"

    @property
    def executable(self) -> Path:
        return self.paths.resolve_project_path(self.config.fxserver_exe)

    @property
    def server_cfg(self) -> Path:
        return self.paths.resolve_project_path(self.config.server_cfg)

    @property
    def txdata_dir(self) -> Path:
        return self.paths.resolve_project_path(self.config.txdata_dir)

    @property
    def log_file(self) -> Path:
        return self.paths.resolve_project_path(self.config.logs_dir) / "fxserver.log"

    def port_owner(self) -> int | None:
        return listening_pid(30120)

    def get_status(self) -> ProcessStatus:
        if not self.executable.exists():
            return ProcessStatus("FXServer", "Error", message="FXServer.exe is missing")
        if not self.txdata_dir.exists():
            return ProcessStatus("FXServer", "Error", message="txData profile directory is missing")
        if not self.server_cfg.exists():
            return ProcessStatus("FXServer", "Error", message="server.cfg is missing")
        pid = read_pid(self.pid_file)
        if pid is None:
            return ProcessStatus("FXServer", "Stopped", message="No manager PID file")
        if is_pid_running(pid):
            return ProcessStatus("FXServer", "Running", pid=pid, message=f"PID {pid}")
        return ProcessStatus("FXServer", "Stopped", pid=pid, message="Stale PID file")

    def create_process(self, parent: QObject) -> QProcess:
        process = QProcess(parent)
        process.setProgram(str(self.executable))
        process.setArguments(["+exec", self.server_cfg.name])
        process.setWorkingDirectory(str(self.txdata_dir))
        process.setProcessChannelMode(QProcess.MergedChannels)
        return process

    def remember_pid(self, pid: int) -> None:
        write_pid(self.pid_file, pid)

    def clear_state(self) -> None:
        clear_pid(self.pid_file)

    def stop(self) -> bool:
        pid = read_pid(self.pid_file)
        if pid is None:
            return True
        stopped = stop_process_tree(pid)
        if stopped or not is_pid_running(pid):
            self.clear_state()
            return True
        return False
