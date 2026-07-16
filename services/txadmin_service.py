from __future__ import annotations

import webbrowser

from core.config import AppConfig


class TxAdminService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def open(self) -> None:
        webbrowser.open(self.config.txadmin_url)
