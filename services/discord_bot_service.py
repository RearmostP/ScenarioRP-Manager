from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QProcess, QObject

from core.config import AppConfig
from core.paths import AppPaths
from core.process import clear_pid, is_pid_running, read_pid, stop_process_tree, write_pid
from models.process_status import ProcessStatus


class DiscordBotService:
    def __init__(self, config: AppConfig, paths: AppPaths) -> None:
        self.config = config
        self.paths = paths
        self.pid_file = self.paths.manager_dir / "state" / "discord-bot.pid"

    @property
    def python_path(self) -> Path:
        return self.paths.resolve_project_path(self.config.discord_bot_python)

    @property
    def bot_file(self) -> Path:
        return self.paths.resolve_project_path(self.config.discord_bot_file)

    @property
    def bot_dir(self) -> Path:
        return self.paths.resolve_project_path(self.config.discord_bot_dir)

    @property
    def log_file(self) -> Path:
        return self.paths.resolve_project_path(self.config.logs_dir) / "discord-bot.log"

    def get_status(self) -> ProcessStatus:
        if not self.python_path.exists() or not self.bot_file.exists():
            return ProcessStatus("Discord Bot", "Error", message="Bot Python or bot.py is missing")
        pid = read_pid(self.pid_file)
        if pid is None:
            return ProcessStatus("Discord Bot", "Stopped", message="No manager PID file")
        if is_pid_running(pid):
            return ProcessStatus("Discord Bot", "Running", pid=pid, message=f"PID {pid}")
        return ProcessStatus("Discord Bot", "Stopped", pid=pid, message="Stale PID file")

    def create_process(self, parent: QObject) -> QProcess:
        process = QProcess(parent)
        process.setProgram(str(self.python_path))
        process.setArguments([str(self.bot_file)])
        process.setWorkingDirectory(str(self.bot_dir))
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
