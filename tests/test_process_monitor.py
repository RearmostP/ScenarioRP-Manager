from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.config import AppConfig
from app.paths import AppPaths
from app.services.process_monitor import ComponentStatus, ProcessMonitor


class StubProcessMonitor(ProcessMonitor):
    def __init__(self, config: AppConfig, paths: AppPaths) -> None:
        super().__init__(config, paths)
        self.open_ports: set[tuple[str, int]] = set()
        self.fxserver_state = "Stopped"

    def _tcp_port_open(self, host: str, port: int) -> bool:
        return (host, port) in self.open_ports

    def fxserver_status(self) -> ComponentStatus:
        return ComponentStatus("FXServer", self.fxserver_state, "test")


class ProcessMonitorServerStatusTests(unittest.TestCase):
    def _monitor(self, server_cfg: Path) -> StubProcessMonitor:
        config = AppConfig(
            fxserver_exe="server/FXServer.exe",
            txdata_dir="txData/ScenarioRP",
            server_cfg=str(server_cfg),
            discord_bot_dir="discord/print_ip_server",
            discord_bot_python="discord/print_ip_server/.venv/Scripts/python.exe",
            discord_bot_file="discord/print_ip_server/bot.py",
            txadmin_profile="default",
            txadmin_url="http://127.0.0.1:40120",
            logs_dir="ScenarioRP-Manager/logs",
            backups_dir="backups",
        )
        paths = AppPaths(manager_dir=server_cfg.parent, project_root=server_cfg.parent)
        return StubProcessMonitor(config, paths)

    def test_server_status_uses_server_port_without_discord_bot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server_cfg = Path(directory) / "server.cfg"
            server_cfg.write_text('endpoint_add_tcp "0.0.0.0:30120"', encoding="utf-8")
            monitor = self._monitor(server_cfg)
            monitor.open_ports.add(("127.0.0.1", 30120))

            status = monitor.server_status()

            self.assertEqual(status.state, "Online")
            self.assertIn("Listening on 127.0.0.1:30120", status.message)

    def test_server_status_is_starting_when_fxserver_runs_but_port_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server_cfg = Path(directory) / "server.cfg"
            server_cfg.write_text('endpoint_add_tcp "0.0.0.0:30120"', encoding="utf-8")
            monitor = self._monitor(server_cfg)
            monitor.fxserver_state = "Running"

            status = monitor.server_status()

            self.assertEqual(status.state, "Starting")

    def test_server_status_is_offline_after_online_server_port_closes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server_cfg = Path(directory) / "server.cfg"
            server_cfg.write_text('endpoint_add_tcp "0.0.0.0:30120"', encoding="utf-8")
            monitor = self._monitor(server_cfg)
            monitor.fxserver_state = "Running"
            monitor.open_ports.add(("127.0.0.1", 30120))

            self.assertEqual(monitor.server_status().state, "Online")

            monitor.open_ports.clear()
            status = monitor.server_status()

            self.assertEqual(status.state, "Offline")

    def test_server_status_is_offline_when_no_port_no_fxserver_no_bot_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server_cfg = Path(directory) / "server.cfg"
            server_cfg.write_text('endpoint_add_tcp "0.0.0.0:30120"', encoding="utf-8")
            monitor = self._monitor(server_cfg)

            status = monitor.server_status()

            self.assertEqual(status.state, "Offline")


if __name__ == "__main__":
    unittest.main()
