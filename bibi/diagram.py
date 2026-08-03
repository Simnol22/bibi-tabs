"""A chord shape as an SVG fret diagram.

Emitted as <symbol> definitions once per distinct chord, so a sheet using five
chords carries five diagrams rather than one per occurrence.
"""

from __future__ import annotations

from .fingering import Shape, shapes

_LEFT = 28  # room for the fret marker, e.g. "2fr"
_RIGHT = 10
_STRING_GAP = 15
_FRET_GAP = 19
_TOP = 20  # room for the open/muted markers above the nut
_STRINGS = 6
#: Every shape in the dataset fits four frets, so the box is a fixed size.
_FRETS = 4
WIDTH = _LEFT + _RIGHT + _STRING_GAP * (_STRINGS - 1)
HEIGHT = _TOP + _FRET_GAP * _FRETS + 6


def symbol_id(index: int) -> str:
    return f"chord-{index}"


def symbol(shape: Shape, index: int) -> str:
    """One diagram, as a reusable <symbol>.

    A barre is drawn plain, with no number repeated across the strings it
    covers. One fret marker sits in the left margin instead -- beside the barre
    when there is one, otherwise beside the top row when the diagram starts
    part-way up the neck. It reads "2fr", so it can never be mistaken for a
    finger number.
    """
    x = lambda s: _LEFT + s * _STRING_GAP  # noqa: E731
    y = lambda f: _TOP + (f - 0.5) * _FRET_GAP  # noqa: E731
    right = _LEFT + _STRING_GAP * (_STRINGS - 1)
    barred = set(shape.barres)

    parts = [
        f'<symbol id="{symbol_id(index)}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        # The nut is heavy only when the diagram starts at the top of the neck.
        f'<line x1="{_LEFT - 1}" y1="{_TOP}" x2="{right + 1}" y2="{_TOP}" '
        f'stroke="currentColor" stroke-width="{4 if shape.base_fret == 1 else 1.2}"/>',
    ]
    for f in range(1, _FRETS + 1):
        parts.append(
            f'<line x1="{_LEFT}" y1="{_TOP + f * _FRET_GAP}" x2="{right}" '
            f'y2="{_TOP + f * _FRET_GAP}" stroke="currentColor" stroke-width="1.2" opacity=".5"/>'
        )
    for s in range(_STRINGS):
        parts.append(
            f'<line x1="{x(s)}" y1="{_TOP}" x2="{x(s)}" y2="{_TOP + _FRETS * _FRET_GAP}" '
            f'stroke="currentColor" stroke-width="1.2" opacity=".5"/>'
        )

    marker = _fret_marker(shape)
    if marker:
        row, fret = marker
        parts.append(
            f'<text x="{_LEFT - 6}" y="{y(row) + 3.5}" font-size="9.5" font-weight="600" '
            f'text-anchor="end" fill="currentColor" opacity=".8">{fret}fr</text>'
        )

    for fret in shape.barres:
        held = [i for i, f in enumerate(shape.frets) if f == fret]
        if held:
            parts.append(
                f'<line x1="{x(min(held))}" y1="{y(fret)}" x2="{x(max(held))}" y2="{y(fret)}" '
                f'stroke="currentColor" stroke-width="11" stroke-linecap="round"/>'
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


def _fret_marker(shape: Shape) -> tuple[int, int] | None:
    """Which row to label, and the real fret it is -- or None if there is
    nothing worth saying.

    A barre is the thing a player positions first, so it gets the label. Failing
    that, a diagram starting part-way up the neck labels its top row. An open
    shape starting at the nut needs neither.
    """
    if shape.barres:
        row = min(shape.barres)
        return row, shape.base_fret + row - 1
    if shape.base_fret > 1:
        return 1, shape.base_fret
    return None


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
