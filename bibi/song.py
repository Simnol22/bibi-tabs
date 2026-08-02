"""A song: some metadata, and lines that are either chords or lyrics."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Close enough to catch real chord symbols and reject ordinary words.
_ROOT = r"[A-G][#b]?"
_QUALITY = r"(?:maj|min|dim|aug|M|m|°|ø|\+|-)?"
_EXT = r"(?:sus|add|maj|min|dim|aug|alt|\d|[#b()+\-°ø])*"
_CHORD = re.compile(rf"^{_ROOT}{_QUALITY}{_EXT}(?:/{_ROOT})?$")

#: A line counts as chords when this share of its tokens parse as chord symbols.
_CHORD_LINE_SHARE = 0.8


def looks_like_chords(text: str) -> bool:
    """True when a line is a chord line rather than a lyric.

    Only ever used to decide styling, so a wrong answer is a mis-coloured line,
    never mangled text.
    """
    tokens = text.split()
    if not tokens:
        return False
    hits = sum(1 for token in tokens if _CHORD.match(token))
    return hits / len(tokens) >= _CHORD_LINE_SHARE


@dataclass(frozen=True)
class Line:
    text: str

    @property
    def is_chords(self) -> bool:
        return looks_like_chords(self.text)


@dataclass(frozen=True)
class SearchResult:
    """One candidate sheet. Deliberately says nothing about where it came from."""

    title: str
    artist: str
    url: str
    version: int = 0
    rating: float = 0.0
    votes: int = 0


@dataclass(frozen=True)
class Song:
    title: str
    artist: str = ""
    capo: int = 0
    key: str = ""
    source: str = ""
    body: str = ""

    #: Header keys written to disk, in this order.
    _FIELDS = ("title", "artist", "capo", "key", "source")

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
            body=body,
        )
