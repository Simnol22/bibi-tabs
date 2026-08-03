"""The sites we can read, and picking the right one for a URL.

No abstract base class: two classes with the same three methods is what duck
typing is for, and an interface for two implementations is guesswork about the
third. Add a source by putting it in the list.
"""

from __future__ import annotations

from .boite_a_chansons import BoiteAChansons
from .song import SearchResult, Song
from .ultimate_guitar import NotAChordPage, UltimateGuitar


class Sources:
    def __init__(self, sources: list | None = None) -> None:
        self.all = sources if sources is not None else [UltimateGuitar(), BoiteAChansons()]

    def matches(self, url: str) -> bool:
        return self.for_url(url) is not None

    def for_url(self, url: str):  # noqa: ANN201 - duck-typed, no shared base
        for source in self.all:
            if source.matches(url):
                return source
        return None

    def name_for(self, url: str) -> str:
        source = self.for_url(url)
        return source.name if source else ""

    def fetch(self, url: str) -> Song:
        source = self.for_url(url)
        if source is None:
            raise NotAChordPage("no source handles that url")
        return source.fetch(url)

    def search(self, query: str) -> list[SearchResult]:
        """Ask every site, and keep going if one of them is down or broken.

        Interleaved so neither site's results bury the other's -- UG returns
        dozens for a well-known song, Boîte à Chansons a handful.
        """
        per_site = []
        for source in self.all:
            try:
                per_site.append(source.search(query))
            except (NotAChordPage, OSError, ValueError):
                per_site.append([])

        merged: list[SearchResult] = []
        for rank in range(max((len(r) for r in per_site), default=0)):
            for results in per_site:
                if rank < len(results):
                    merged.append(results[rank])
        return merged
