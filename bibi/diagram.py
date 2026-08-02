"""A chord shape as an SVG fret diagram.

Emitted as <symbol> definitions once per distinct chord, so a sheet using five
chords carries five diagrams rather than one per occurrence.
"""

from __future__ import annotations

from .fingering import Shape, shapes

_PAD = 18  # margins hold the barre finger on the left, the base fret on the right
_STRING_GAP = 15
_FRET_GAP = 19
_TOP = 20  # room for the open/muted markers above the nut
_STRINGS = 6
#: Every shape in the dataset fits four frets, so the box is a fixed size.
_FRETS = 4
WIDTH = _PAD * 2 + _STRING_GAP * (_STRINGS - 1)
HEIGHT = _TOP + _FRET_GAP * _FRETS + 6


def symbol_id(index: int) -> str:
    return f"chord-{index}"


def symbol(shape: Shape, index: int) -> str:
    """One diagram, as a reusable <symbol>.

    A barre is one finger doing one thing, so it gets one number in the left
    margin rather than the same digit repeated across every string it covers.
    The base fret sits in the right margin, so the two never collide.
    """
    x = lambda s: _PAD + s * _STRING_GAP  # noqa: E731
    y = lambda f: _TOP + (f - 0.5) * _FRET_GAP  # noqa: E731
    barred = set(shape.barres)

    parts = [
        f'<symbol id="{symbol_id(index)}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        # The nut is heavy only when the diagram starts at the top of the neck.
        f'<line x1="{_PAD - 1}" y1="{_TOP}" x2="{WIDTH - _PAD + 1}" y2="{_TOP}" '
        f'stroke="currentColor" stroke-width="{4 if shape.base_fret == 1 else 1.2}"/>',
    ]
    for f in range(1, _FRETS + 1):
        parts.append(
            f'<line x1="{_PAD}" y1="{_TOP + f * _FRET_GAP}" x2="{WIDTH - _PAD}" '
            f'y2="{_TOP + f * _FRET_GAP}" stroke="currentColor" stroke-width="1.2" opacity=".5"/>'
        )
    for s in range(_STRINGS):
        parts.append(
            f'<line x1="{x(s)}" y1="{_TOP}" x2="{x(s)}" y2="{_TOP + _FRETS * _FRET_GAP}" '
            f'stroke="currentColor" stroke-width="1.2" opacity=".5"/>'
        )
    if shape.base_fret > 1:
        parts.append(
            f'<text x="{WIDTH - _PAD + 4}" y="{y(1) + 3}" font-size="10" '
            f'fill="currentColor" opacity=".7">{shape.base_fret}</text>'
        )

    for fret in shape.barres:
        held = [i for i, f in enumerate(shape.frets) if f == fret]
        if not held:
            continue
        parts.append(
            f'<line x1="{x(min(held))}" y1="{y(fret)}" x2="{x(max(held))}" y2="{y(fret)}" '
            f'stroke="currentColor" stroke-width="11" stroke-linecap="round"/>'
        )
        finger = _barre_finger(shape, held)
        if finger:
            parts.append(
                f'<text x="{_PAD - 7}" y="{y(fret) + 3.5}" font-size="10" font-weight="700" '
                f'text-anchor="end" fill="currentColor">{finger}</text>'
            )

    for s, fret in enumerate(shape.frets):
        if fret < 0 or fret == 0:
            parts.append(
                f'<text x="{x(s)}" y="{_TOP - 6}" font-size="11" text-anchor="middle" '
                f'fill="currentColor" opacity=".7">{"○" if fret == 0 else "×"}</text>'
            )
            continue
        if fret in barred:
            continue  # the barre already draws it, and its number is in the margin
        parts.append(f'<circle cx="{x(s)}" cy="{y(fret)}" r="5.5" fill="currentColor"/>')
        # Some rows use -1 rather than 0 for "no finger"; both mean no number.
        finger = shape.fingers[s] if s < len(shape.fingers) else 0
        if finger > 0:
            parts.append(
                f'<text x="{x(s)}" y="{y(fret) + 3}" font-size="8" font-weight="700" '
                f'text-anchor="middle" fill="var(--bg)">{finger}</text>'
            )

    parts.append("</symbol>")
    return "".join(parts)


def _barre_finger(shape: Shape, held: list[int]) -> int:
    """Which finger lays the barre. Usually 1, but the data uses 2, 3 and 4 too."""
    for s in held:
        if s < len(shape.fingers) and shape.fingers[s] > 0:
            return shape.fingers[s]
    return 0


class Diagrams:
    """Collects the distinct chords on a sheet and hands out symbol ids."""

    def __init__(self) -> None:
        self._ids: dict[str, int] = {}
        self._symbols: list[str] = []

    def add(self, token: str) -> str | None:
        """Register a chord, returning its symbol id, or None if unknown."""
        if token in self._ids:
            return symbol_id(self._ids[token])

        found = shapes(token)
        if not found:
            return None
        index = len(self._symbols)
        self._ids[token] = index
        self._symbols.append(symbol(found[0], index))
        return symbol_id(index)

    def defs(self) -> str:
        if not self._symbols:
            return ""
        return f'<svg class="defs" aria-hidden="true">{"".join(self._symbols)}</svg>'
