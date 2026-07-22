from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.core.config import load_config
from app.paths import AppPaths
from app.ui.main_window import MainWindow


def main() -> int:
    paths = AppPaths.discover()
    config = load_config(paths.system("config.json"))

    app = QApplication(sys.argv)
    icon_path = paths.asset("ScenarioRP_48x48.ico")
    if not icon_path.exists():
        icon_path = paths.asset("myLogo.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(config=config, paths=paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
