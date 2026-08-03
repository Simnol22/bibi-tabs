"""Chord symbols, and moving them up and down.

Everything here is pure: no I/O, no state. Transposition is a display-time
transform -- the stored song is never rewritten, so a song always opens in the
key it was written in.

Only the root and the bass carry pitch. Quality and extension ride along as
opaque text, so `m7b5` needs no understanding to survive a transposition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
_LETTER = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

#: The practical keys along the circle of fifths. Index minus 7 is the signature,
#: negative for flats. Spelling follows the key, never a fixed table -- otherwise
#: a transposed sheet reads Gb where F# belongs.
_MAJOR = ["Cb", "Gb", "Db", "Ab", "Eb", "Bb", "F", "C", "G", "D", "A", "E", "B", "F#", "C#"]
_MINOR = ["Abm", "Ebm", "Bbm", "Fm", "Cm", "Gm", "Dm", "Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "A#m"]

_ROOT = r"[A-G][#b]?"
_QUALITY = r"(?:maj|min|dim|aug|M|m|°|ø|\+|-)?"
_EXT = r"(?:sus|add|maj|min|dim|aug|alt|\d|[#b()+\-°ø])*"
_CHORD = re.compile(rf"^({_ROOT})({_QUALITY})({_EXT})(?:/({_ROOT}))?$")

#: A line counts as chords when this share of its tokens parse as chord symbols.
_CHORD_LINE_SHARE = 0.8
#: Bar lines, repeat marks and beat slashes. Neither chord nor word.
_BAR = re.compile(r"^[|:/%]+$")

MAX_TRANSPOSE = 11


def split_wrap(token: str) -> tuple[str, str, str]:
    """Peel a bracket that wraps a whole chord: `(Dmaj7)` is an optional Dmaj7.

    Distinct from a bracket *inside* a chord, as in `C(add9)`, which is part of
    the symbol and is left alone.
    """
    for opener, closer in (("(", ")"), ("[", "]")):
        if len(token) > 2 and token.startswith(opener) and token.endswith(closer):
            return opener, token[1:-1], closer
    return "", token, ""


def chord_in(token: str) -> Chord | None:
    """The chord a token carries, ignoring any bracket around it."""
    return Chord.parse(split_wrap(token)[1])


def unambiguous_chord(token: str) -> Chord | None:
    """A chord whose spelling could not also be an ordinary word.

    `Dmaj7` or `A7sus4` is a chord wherever it appears. A lone `A`, or `Am`, is
    a word far more often, so those only count on a line already read as chords.
    """
    core = split_wrap(token)[1]
    if len(core) < 2 or core == "Am":
        return None
    return Chord.parse(core)


def looks_like_chords(text: str) -> bool:
    """True when a line is a chord line rather than a lyric.

    Bar lines and beat marks count neither way -- "| C | G |" is a chord line,
    and counting the bars against it would drag it under the threshold.
    """
    tokens = [t for t in text.split() if not _BAR.match(t)]
    if not tokens:
        return False
    hits = sum(1 for token in tokens if chord_in(token))
    return hits / len(tokens) >= _CHORD_LINE_SHARE


def pitch_class(note: str) -> int:
    pitch = _LETTER[note[0].upper()]
    for accidental in note[1:]:
        pitch += 1 if accidental == "#" else -1
    return pitch % 12


def key_signature(key: str) -> int | None:
    """Sharps positive, flats negative. None if it isn't a key we know."""
    table = _MINOR if key.endswith("m") else _MAJOR
    return table.index(key) - 7 if key in table else None


def transpose_key(key: str, semitones: int) -> str:
    """Shift a key, choosing the most readable spelling of the destination.

    Fewest accidentals wins -- up a semitone from A is Bb, never A#, which would
    need ten sharps. Where two spellings tie at six, keep heading the way the
    source key was already going.
    """
    signature = key_signature(key)
    if signature is None:
        return key

    minor = key.endswith("m")
    table = _MINOR if minor else _MAJOR
    tonic = (pitch_class(key[:-1] if minor else key) + semitones) % 12
    candidates = [k for k in table if pitch_class(k[:-1] if minor else k) == tonic]

    def rank(candidate: str) -> tuple[int, int]:
        own = key_signature(candidate) or 0
        # Tie-break towards the direction the source key already leaned.
        wrong_way = (own < 0) != (signature < 0)
        return abs(own), int(wrong_way)

    return min(candidates, key=rank) if candidates else key


def lay_out(placements: list[tuple[int, str]]) -> str:
    """Put each token at its column, pushing right by the minimum on collision.

    Shared by the transposer (a shifted chord can be wider than the one it
    replaces) and by sources that anchor chords inline rather than by column.
    Letting one collision shove everything after it would drift the whole line.
    """
    out = ""
    for column, token in placements:
        start = column if not out else max(column, len(out) + 1)
        out = out.ljust(start) + token
    return out


@dataclass(frozen=True)
class Chord:
    root: str
    quality: str = ""
    ext: str = ""
    bass: str | None = None

    @classmethod
    def parse(cls, token: str) -> Chord | None:
        match = _CHORD.match(token)
        if not match:
            return None
        return cls(match.group(1), match.group(2) or "", match.group(3) or "", match.group(4))

    def transposed(self, semitones: int, flats: bool) -> Chord:
        table = _FLAT if flats else _SHARP
        shift = lambda note: table[(pitch_class(note) + semitones) % 12]  # noqa: E731
        return Chord(
            root=shift(self.root),
            quality=self.quality,
            ext=self.ext,
            bass=None if self.bass is None else shift(self.bass),
        )

    def __str__(self) -> str:
        slash = "" if self.bass is None else f"/{self.bass}"
        return f"{self.root}{self.quality}{self.ext}{slash}"


class Transposer:
    """Shifts the chord lines of one song by a fixed number of semitones."""

    def __init__(self, semitones: int, flats: bool = False) -> None:
        self.semitones = semitones
        self.flats = flats

    @classmethod
    def for_song(cls, key: str, body: str, semitones: int) -> Transposer:
        """Spell from the key the song is heading *to*, not the one it left."""
        target = transpose_key(key, semitones) if key else ""
        signature = key_signature(target) if target else None
        if signature is None:
            # No usable key: follow whichever accidental the sheet already uses.
            signature = -1 if body.count("b") > body.count("#") else 1
        return cls(semitones, flats=signature < 0)

    def token(self, token: str) -> str:
        opener, core, closer = split_wrap(token)
        chord = Chord.parse(core)
        if chord is None:
            return token
        return f"{opener}{chord.transposed(self.semitones, self.flats)}{closer}"

    def line(self, text: str) -> str:
        """Re-anchor every chord at the column it started in.

        A transposed chord can be wider (C -> C#) or narrower (Bb -> B), and the
        column is the only thing tying a chord to its syllable. Where a widened
        chord would collide with the next, the next moves right by the minimum,
        which beats letting everything after it drift.
        """
        if self.semitones == 0:
            return text
        return lay_out(
            [(m.start(), self.token(m.group())) for m in re.finditer(r"\S+", text)]
        )
