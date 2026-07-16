from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.config import load_config
from core.paths import AppPaths
from ui.main_window import MainWindow


def main() -> int:
    paths = AppPaths.discover()
    config = load_config(paths.manager_dir / "config.json")

    app = QApplication(sys.argv)
    icon_path = paths.resolve_project_path("txData/ScenarioRP/myLogo.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(config=config, paths=paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
