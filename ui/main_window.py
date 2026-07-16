from __future__ import annotations

import re
from datetime import datetime
from typing import TypeVar

from PySide6.QtCore import QFile, QProcess, QTimer
from PySide6.QtGui import QFont
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QMainWindow, QPlainTextEdit, QPushButton, QWidget

from core.config import AppConfig
from core.paths import AppPaths
from services.discord_bot_service import DiscordBotService
from services.environment_service import EnvironmentService
from services.fxserver_service import FXServerService
from services.txadmin_service import TxAdminService


WidgetT = TypeVar("WidgetT", bound=QWidget)
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig, paths: AppPaths) -> None:
        super().__init__()
        self.config = config
        self.paths = paths
        self.environment_service = EnvironmentService(config, paths)
        self.fxserver_service = FXServerService(config, paths)
        self.discord_bot_service = DiscordBotService(config, paths)
        self.txadmin_service = TxAdminService(config)
        self.fx_process: QProcess | None = None
        self.bot_process: QProcess | None = None
        self.manager_log_file = self.paths.resolve_project_path(self.config.logs_dir) / "manager.log"

        self._load_designer_ui()
        self._load_styles()
        self._bind_widgets()
        self._connect_signals()
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh)
        self.status_timer.start(2000)
        self.refresh()

    def _load_designer_ui(self) -> None:
        ui_path = self.paths.manager_dir / "ui" / "main_window.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Could not open UI file: {ui_path}")

        self._ui_loader = QUiLoader()
        loaded = self._ui_loader.load(ui_file, self)
        ui_file.close()
        if loaded is None:
            raise RuntimeError(f"Could not load UI file: {ui_path}")
        if not isinstance(loaded, QWidget):
            raise RuntimeError(f"Expected QWidget in UI file: {ui_path}")

        self.setWindowTitle("ScenarioRP Manager")
        self.resize(loaded.size())
        self.setCentralWidget(loaded)
        self._designer_widget = loaded

    def _load_styles(self) -> None:
        qss_path = self.paths.manager_dir / "ui" / "styles.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _widget(self, name: str, widget_type: type[WidgetT]) -> WidgetT:
        widget = self.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"Missing widget in main_window.ui: {name}")
        return widget

    def _bind_widgets(self) -> None:
        self.project_root_label = self._widget("projectRootLabel", QLabel)

        self.start_button = self._widget("startButton", QPushButton)
        self.stop_button = self._widget("stopButton", QPushButton)
        self.restart_button = self._widget("restartButton", QPushButton)
        self.safe_shutdown_button = self._widget("safeShutdownButton", QPushButton)
        self.txadmin_button = self._widget("txadminButton", QPushButton)

        self.fx_state_label = self._widget("fxStateLabel", QLabel)
        self.fx_message_label = self._widget("fxMessageLabel", QLabel)
        self.bot_state_label = self._widget("botStateLabel", QLabel)
        self.bot_message_label = self._widget("botMessageLabel", QLabel)
        self.environment_state_label = self._widget("environmentStateLabel", QLabel)
        self.environment_message_label = self._widget("environmentMessageLabel", QLabel)
        self.txadmin_state_label = self._widget("txadminStateLabel", QLabel)
        self.txadmin_message_label = self._widget("txadminMessageLabel", QLabel)
        self.database_state_label = self._widget("databaseStateLabel", QLabel)
        self.database_message_label = self._widget("databaseMessageLabel", QLabel)
        self.log_viewer = self._widget("logViewer", QPlainTextEdit)

        self.project_root_label.setText(str(self.paths.project_root))
        self.log_viewer.setFont(QFont("Consolas", 10))
        self.log_viewer.setReadOnly(True)

    def _connect_signals(self) -> None:
        self.txadmin_button.clicked.connect(self.txadmin_service.open)
        self.start_button.clicked.connect(self.start_all)
        self.stop_button.clicked.connect(self.stop_all)
        self.restart_button.clicked.connect(self.restart_all)
        self.safe_shutdown_button.clicked.connect(self.safe_shutdown)

    def _set_status(self, state_label: QLabel, message_label: QLabel, state: str, message: str) -> None:
        state_label.setText(state)
        message_label.setText(message)

    def _append_log(self, source: str, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} | INFO | {source} | {message}"
        self.manager_log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.manager_log_file.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self.log_viewer.appendPlainText(line)
        self.log_viewer.verticalScrollBar().setValue(self.log_viewer.verticalScrollBar().maximum())

    def _append_process_output(self, source: str, log_file, process: QProcess) -> None:
        data = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not data.strip():
            return
        clean_data = ANSI_PATTERN.sub("", data)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(clean_data)
        for line in clean_data.rstrip().splitlines():
            self._append_log(source, line)

    def _set_actions_enabled(self, enabled: bool) -> None:
        for button in [self.start_button, self.stop_button, self.restart_button, self.safe_shutdown_button, self.txadmin_button]:
            button.setEnabled(enabled)

    def _has_missing_environment(self) -> bool:
        checks = self.environment_service.run_basic_checks()
        failed_checks = [check for check in checks if not check.status]
        for check in failed_checks:
            self._append_log("Environment", check.message)
        return bool(failed_checks)

    def start_all(self) -> None:
        if self._has_missing_environment():
            self._append_log("Manager", "Start aborted because required paths are missing")
            self.refresh()
            return

        self._set_actions_enabled(False)
        self._append_log("Manager", "Starting ScenarioRP")

        fx_status = self.fxserver_service.get_status()
        if fx_status.state != "Running":
            port_owner = self.fxserver_service.port_owner()
            if port_owner is not None:
                self._append_log("FXServer", f"Start aborted: port 30120 is already in use by PID {port_owner}")
                self._set_actions_enabled(True)
                self.refresh()
                return

        if fx_status.state == "Running":
            self._append_log("FXServer", f"Already running with PID {fx_status.pid}")
            self._start_bot_after_fx()
            return

        self.fx_process = self.fxserver_service.create_process(self)
        self.fx_process.readyReadStandardOutput.connect(
            lambda: self._append_process_output("FXServer", self.fxserver_service.log_file, self.fx_process)
        )
        self.fx_process.started.connect(self._fx_started)
        self.fx_process.finished.connect(self._fx_finished)
        self.fx_process.start()

    def _fx_started(self) -> None:
        if self.fx_process is None:
            return
        pid = int(self.fx_process.processId())
        self.fxserver_service.remember_pid(pid)
        self._append_log("FXServer", f"Process started with PID {pid}")
        self.refresh()
        QTimer.singleShot(2500, self._start_bot_if_fx_still_running)

    def _start_bot_if_fx_still_running(self) -> None:
        fx_status = self.fxserver_service.get_status()
        if fx_status.state != "Running":
            self._append_log("FXServer", f"Discord bot start skipped because FXServer is not running: {fx_status.message}")
            self._set_actions_enabled(True)
            self.refresh()
            return
        self._start_bot_after_fx()

    def _fx_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._append_log("FXServer", f"Process finished with exit code {exit_code}, status {exit_status.name}")
        self.fxserver_service.clear_state()
        self.refresh()

    def _start_bot_after_fx(self) -> None:
        bot_status = self.discord_bot_service.get_status()
        if bot_status.state == "Running":
            self._append_log("DiscordBot", f"Already running with PID {bot_status.pid}")
            self._set_actions_enabled(True)
            self.refresh()
            return

        self.bot_process = self.discord_bot_service.create_process(self)
        self.bot_process.readyReadStandardOutput.connect(
            lambda: self._append_process_output("DiscordBot", self.discord_bot_service.log_file, self.bot_process)
        )
        self.bot_process.started.connect(self._bot_started)
        self.bot_process.finished.connect(self._bot_finished)
        self.bot_process.start()

    def _bot_started(self) -> None:
        if self.bot_process is None:
            return
        pid = int(self.bot_process.processId())
        self.discord_bot_service.remember_pid(pid)
        self._append_log("DiscordBot", f"Process started with PID {pid}")
        self._set_actions_enabled(True)
        self.refresh()

    def _bot_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._append_log("DiscordBot", f"Process finished with exit code {exit_code}, status {exit_status.name}")
        self.discord_bot_service.clear_state()
        self.refresh()

    def stop_all(self) -> None:
        self._set_actions_enabled(False)
        self._append_log("Manager", "Stopping ScenarioRP")

        fx_stopped = self.fxserver_service.stop()
        self._append_log("FXServer", "Stopped" if fx_stopped else "Stop failed")

        bot_stopped = self.discord_bot_service.stop()
        self._append_log("DiscordBot", "Stopped" if bot_stopped else "Stop failed")

        self._set_actions_enabled(True)
        self.refresh()

    def restart_all(self) -> None:
        self._append_log("Manager", "Restarting ScenarioRP")
        self.stop_all()
        QTimer.singleShot(1500, self.start_all)

    def safe_shutdown(self) -> None:
        self._append_log("Manager", "Safe Shutdown requested")
        self.stop_all()
        self._append_log("Manager", "ScenarioRP is safe to close. You may now eject the drive.")

    def refresh(self) -> None:
        fx_status = self.fxserver_service.get_status()
        bot_status = self.discord_bot_service.get_status()
        checks = self.environment_service.run_basic_checks()
        failed_checks = [check for check in checks if not check.status]

        self._set_status(self.fx_state_label, self.fx_message_label, fx_status.state, fx_status.message)
        self._set_status(self.bot_state_label, self.bot_message_label, bot_status.state, bot_status.message)
        self._set_status(
            self.environment_state_label,
            self.environment_message_label,
            "Error" if failed_checks else "OK",
            f"{len(failed_checks)} missing checks" if failed_checks else "All basic paths exist",
        )
        self._set_status(self.txadmin_state_label, self.txadmin_message_label, "Unknown", self.config.txadmin_url)
        self._set_status(self.database_state_label, self.database_message_label, "Unknown", "Implemented in stage 4")

        if self.log_viewer.toPlainText().strip():
            return
        self.log_viewer.appendPlainText("Environment checks:")
        for check in checks:
            state = "OK" if check.status else "ERROR"
            self.log_viewer.appendPlainText(f"{state} | {check.name} | {check.message}")
