from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentCheck:
    name: str
    status: bool
    message: str
    severity: str = "info"
