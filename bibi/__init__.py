"""BIBI-tabs — open a guitar chord sheet from a link, keep it, read it offline."""

from .library import Library
from .render import HtmlRenderer
from .song import Line, Song
from .ultimate_guitar import NotAChordPage, UltimateGuitar

__all__ = ["Library", "HtmlRenderer", "Line", "Song", "NotAChordPage", "UltimateGuitar"]
