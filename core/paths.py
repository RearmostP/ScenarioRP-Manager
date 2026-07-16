from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    manager_dir: Path
    project_root: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        manager_dir = Path(__file__).resolve().parents[1]
        return cls(manager_dir=manager_dir, project_root=manager_dir.parent)

    def resolve_project_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()
