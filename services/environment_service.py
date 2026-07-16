from __future__ import annotations

from core.config import AppConfig
from core.paths import AppPaths
from models.environment_check import EnvironmentCheck


class EnvironmentService:
    def __init__(self, config: AppConfig, paths: AppPaths) -> None:
        self.config = config
        self.paths = paths

    def run_basic_checks(self) -> list[EnvironmentCheck]:
        checks = [
            ("FXServer.exe", self.config.fxserver_exe),
            ("txData profile", self.config.txdata_dir),
            ("server.cfg", self.config.server_cfg),
            ("Discord bot directory", self.config.discord_bot_dir),
            ("Discord bot Python", self.config.discord_bot_python),
            ("Discord bot file", self.config.discord_bot_file),
        ]

        results: list[EnvironmentCheck] = []
        for name, relative_path in checks:
            path = self.paths.resolve_project_path(relative_path)
            exists = path.exists()
            results.append(
                EnvironmentCheck(
                    name=name,
                    status=exists,
                    message=str(path) if exists else f"Missing: {path}",
                    severity="info" if exists else "error",
                )
            )
        return results
