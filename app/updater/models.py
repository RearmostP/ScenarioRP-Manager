from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateRelease:
    """Metadata for an available application update."""

    version: str
    download_url: str
    file_name: str
    release_notes: str | None
    checksum: str | None
    is_prerelease: bool
