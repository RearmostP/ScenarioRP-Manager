from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessStatus:
    name: str
    state: str
    pid: int | None = None
    message: str = ""
