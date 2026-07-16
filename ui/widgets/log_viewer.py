from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPlainTextEdit


class LogViewer(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))

    def append_line(self, text: str) -> None:
        self.appendPlainText(text)
