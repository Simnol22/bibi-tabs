"""Songs on disk. One plain text file each, so they outlive this program."""

from __future__ import annotations

from pathlib import Path

from .song import Song

DEFAULT_HOME = Path.home() / ".bibi-tabs"


class Library:
    def __init__(self, home: Path = DEFAULT_HOME) -> None:
        self.home = home

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
