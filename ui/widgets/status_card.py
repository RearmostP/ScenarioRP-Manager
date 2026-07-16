from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatusCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("Subtitle")
        self.state_label = QLabel("Unknown")
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.state_label)
        layout.addWidget(self.message_label)
        layout.addStretch(1)

    def set_status(self, state: str, message: str) -> None:
        self.state_label.setText(state)
        self.message_label.setText(message)
