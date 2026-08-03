"""Chord symbol -> where your fingers go.

Data is chords-db (MIT, (c) 2016 David Rubert), flattened to "key|suffix" and
stripped of its midi arrays -- see data/LICENSE-chords-db. Bundled rather than
fetched so the diagrams work with no connection.

Separate from chords.py, which is pure theory with no data files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .chords import chord_in, pitch_class

_DATA = Path(__file__).parent / "data" / "guitar.json"

#: The twelve root spellings the dataset indexes on.
_ROOTS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
#: Slash basses are filed under both spellings, so try the other one too.
_ALT = {"C#": "Db", "Eb": "D#", "F#": "Gb", "Ab": "G#", "Bb": "A#"}

_QUALITY = {"": "", "m": "m", "min": "m", "-": "m", "maj": "maj", "M": "maj",
            "dim": "dim", "°": "dim", "aug": "aug", "+": "aug"}

#: Spellings our parser produces that the dataset files differently.
_ALIAS = {"m7-5": "m7b5", "7-5": "7b5", "7#5": "aug7", "7+5": "aug7", "9#5": "aug9"}


@dataclass(frozen=True)
class Shape:
    """One way to play a chord. Six strings, low E first."""

    frets: tuple[int, ...]
    """-1 muted, 0 open, else a fret offset from base_fret."""
    fingers: tuple[int, ...]
    """0 for none, otherwise 1-4."""
    base_fret: int
    barres: tuple[int, ...] = ()


@lru_cache(maxsize=1)
def _db() -> dict[str, list[dict]]:
    return json.loads(_DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=512)
def shapes(token: str) -> tuple[Shape, ...]:
    """Every voicing the dataset knows, most common first. Empty if unknown."""
    chord = chord_in(token)
    if chord is None:
        return ()

    root = _ROOTS[pitch_class(chord.root)]
    for suffix in _candidates(chord):
        found = _db().get(f"{root}|{suffix}")
        if found:
            return tuple(
                Shape(
                    frets=tuple(p["frets"]),
                    fingers=tuple(p["fingers"]),
                    base_fret=p["baseFret"],
                    barres=tuple(p.get("barres") or ()),
                )
                for p in found
            )
    return ()


def _candidates(chord: Chord) -> list[str]:
    """Most specific first. A slash chord the dataset lacks falls back to the
    base shape, which is more use than an empty box."""
    if chord.quality == "ø":
        core = "m7b5"  # half-diminished is filed this way, its 7 implied
    else:
        core = (_QUALITY.get(chord.quality, chord.quality)) + chord.ext
        core = _ALIAS.get(core, core)

    plain = "major" if core == "" else "minor" if core == "m" else core
    if chord.bass is None:
        return [plain]

    bass = _ROOTS[pitch_class(chord.bass)]
    alt = _ALT.get(bass)
    return [f"{core}/{bass}"] + ([f"{core}/{alt}"] if alt else []) + [plain]
