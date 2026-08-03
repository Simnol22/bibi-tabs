"""A song: some metadata, and lines that are either chords or lyrics."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# One definition of "what is a chord", and it lives in chords.py.
from .chords import looks_like_chords

__all__ = ["Line", "SearchResult", "Song", "looks_like_chords"]


@dataclass(frozen=True)
class Line:
    text: str

    @property
    def is_chords(self) -> bool:
        return looks_like_chords(self.text)


@dataclass(frozen=True)
class SearchResult:
    """One candidate sheet, and which site is offering it."""

    title: str
    artist: str
    url: str
    version: int = 0
    rating: float = 0.0
    votes: int = 0
    source: str = ""


@dataclass(frozen=True)
class Song:
    title: str
    artist: str = ""
    capo: int = 0
    key: str = ""
    source: str = ""
    #: Which site it came from, as a name. Blank on songs saved before there
    #: was more than one; they simply show no label until re-saved.
    site: str = ""
    body: str = ""

    #: Header keys written to disk, in this order.
    _FIELDS = ("title", "artist", "capo", "key", "source", "site")

    @property
    def lines(self) -> list[Line]:
        return [Line(text) for text in self.body.split("\n")]

    @property
    def slug(self) -> str:
        stem = f"{self.artist}-{self.title}" if self.artist else self.title
        # Fold accents rather than dropping them, or "Drôle" becomes "dr-le".
        folded = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
        return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", folded.lower())).strip("-")

    def to_text(self) -> str:
        """A readable header, a blank line, then the sheet exactly as it is."""
        header = "\n".join(f"{name}: {getattr(self, name)}" for name in self._FIELDS)
        return f"{header}\n\n{self.body}"

    @classmethod
    def from_text(cls, text: str) -> Song:
        header, _, body = text.replace("\r\n", "\n").partition("\n\n")
        values: dict[str, str] = {}
        for line in header.split("\n"):
            name, _, value = line.partition(":")
            if name.strip() in cls._FIELDS:
                values[name.strip()] = value.strip()
        return cls(
            title=values.get("title", "Untitled"),
            artist=values.get("artist", ""),
            capo=int(values.get("capo") or 0),
            key=values.get("key", ""),
            source=values.get("source", ""),
            site=values.get("site", ""),
            body=body,
        )
