"""Reading a song off an Ultimate Guitar page.

Everything site-specific lives here. When UG redesigns -- and it will -- this is
the only file that should need touching.

The page ships its data as HTML-escaped JSON in a <div class="js-store">. The
sheet itself sits at store.page.data.tab_view.wiki_tab.content, with chords
wrapped in [ch]...[/ch] and aligned sections in [tab]...[/tab]. Those markers are
laid over already-aligned text, so removing them leaves the columns intact.
"""

from __future__ import annotations

import html
import json
import re
import urllib.request

from .song import Song

_STORE = re.compile(r'class="js-store" data-content="(.*?)"></div>', re.S)
_MARKERS = re.compile(r"\[/?(?:ch|tab)\]")
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class NotAChordPage(Exception):
    """The URL loaded, but there is no chord sheet in it."""


class UltimateGuitar:
    """Fetches a UG page and turns it into a Song."""

    def matches(self, url: str) -> bool:
        return "ultimate-guitar.com" in url

    def fetch(self, url: str) -> Song:
        return self.parse(self._download(url), url)

    def parse(self, page: str, url: str = "") -> Song:
        match = _STORE.search(page)
        if not match:
            raise NotAChordPage("no js-store block -- the page layout has changed")

        data = json.loads(html.unescape(match.group(1)))["store"]["page"]["data"]
        tab = data.get("tab", {})
        view = data.get("tab_view", {})
        content = view.get("wiki_tab", {}).get("content")
        if not content:
            raise NotAChordPage("no tab content -- is this a Pro tab, or tabs not chords?")

        return Song(
            title=tab.get("song_name") or "Untitled",
            artist=tab.get("artist_name") or "",
            capo=int(view.get("meta", {}).get("capo") or 0),
            key=tab.get("tonality_name") or "",
            source=url,
            body=self._clean(content),
        )

    def _clean(self, content: str) -> str:
        return _MARKERS.sub("", content).replace("\r\n", "\n").strip("\n")

    def _download(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
