"""Songs on disk. One plain text file each, so they outlive this program."""

from __future__ import annotations

import shutil
from pathlib import Path

from .config import Config
from .song import Song


class Library:
    def __init__(self, home: Path | None = None) -> None:
        #: Reading the setting here means every entry point honours it.
        self.home = home if home is not None else Config().library

    def move_to(self, new_home: Path) -> int:
        """Take the songs along when the folder changes. Returns how many moved.

        shutil.move rather than rename: the new folder may be on another disk.
        A name already present at the destination is left alone rather than
        silently overwritten.
        """
        if new_home == self.home:
            return 0
        new_home.mkdir(parents=True, exist_ok=True)
        moved = 0
        for path in self.paths():
            target = new_home / path.name
            if not target.exists():
                shutil.move(str(path), str(target))
                moved += 1
        return moved

    def path_for(self, song: Song) -> Path:
        return self.home / f"{song.slug}.txt"

    def save(self, song: Song) -> Path:
        self.home.mkdir(parents=True, exist_ok=True)
        path = self.path_for(song)
        path.write_text(song.to_text(), encoding="utf-8")
        return path

    def load(self, path: Path) -> Song:
        return Song.from_text(path.read_text(encoding="utf-8"))

    def paths(self) -> list[Path]:
        if not self.home.is_dir():
            return []
        return sorted(self.home.glob("*.txt"))

    def delete(self, slug: str) -> bool:
        """Really delete. Local files, no sync, so nothing to tombstone."""
        path = self.path_for_slug(slug)
        if path is None:
            return False
        path.unlink()
        return True

    def path_for_slug(self, slug: str) -> Path | None:
        """Exact lookup. Rejects anything with a path separator in it."""
        if not slug or "/" in slug or "\\" in slug or slug.startswith("."):
            return None
        path = self.home / f"{slug}.txt"
        return path if path.is_file() else None

    def find(self, query: str) -> Path | None:
        """First file whose name contains every word of the query."""
        words = query.lower().split()
        for path in self.paths():
            if all(word in path.stem.lower() for word in words):
                return path
        return None
