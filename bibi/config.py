"""Settings. One small JSON file, one setting so far.

Kept outside the song folder for the obvious reason: the song folder is the
thing it points at.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_LIBRARY = Path.home() / ".bibi-tabs"


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "bibi-tabs.json"


class Config:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path()

    @property
    def library(self) -> Path:
        stored = self._read().get("library")
        return Path(stored).expanduser() if stored else DEFAULT_LIBRARY

    def set_library(self, home: Path) -> None:
        data = self._read()
        data["library"] = str(home)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _read(self) -> dict:
        """A missing or broken config is not an error -- fall back to defaults."""
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
