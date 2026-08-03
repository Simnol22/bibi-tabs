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
import urllib.parse
import urllib.request

from .song import SearchResult, Song

_STORE = re.compile(r'class="js-store" data-content="(.*?)"></div>', re.S)
_MARKERS = re.compile(r"\[/?(?:ch|tab)\]")
_SEARCH = "https://www.ultimate-guitar.com/search.php?search_type=title&value={}"
_HOST = "ultimate-guitar.com"
_SHEET_HOST = "tabs.ultimate-guitar.com"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class NotAChordPage(Exception):
    """The URL loaded, but there is no chord sheet in it."""


class UltimateGuitar:
    """Fetches a UG page and turns it into a Song."""

    name = "Ultimate Guitar"

    def matches(self, url: str) -> bool:
        """Strict on purpose -- the local server fetches whatever this approves.

        Substring matching would wave through evil-ultimate-guitar.com.
        """
        try:
            parsed = urllib.parse.urlparse(url)
        except ValueError:
            return False
        host = (parsed.hostname or "").lower()
        return parsed.scheme in ("http", "https") and (
            host == _HOST or host.endswith(f".{_HOST}")
        )

    def fetch(self, url: str) -> Song:
        if not self.matches(url):
            raise NotAChordPage(f"not an Ultimate Guitar url: {url}")
        return self.parse(self._download(url), url)

    def search(self, query: str) -> list[SearchResult]:
        page = self._download(_SEARCH.format(urllib.parse.quote(query)))
        return self.parse_search(page)

    def parse_search(self, page: str) -> list[SearchResult]:
        match = _STORE.search(page)
        if not match:
            raise NotAChordPage("no js-store block -- the search layout has changed")

        data = json.loads(html.unescape(match.group(1)))["store"]["page"]["data"]
        found = [
            SearchResult(
                title=item.get("song_name") or "Untitled",
                artist=item.get("artist_name") or "",
                url=item["tab_url"],
                version=int(item.get("version") or 0),
                rating=float(item.get("rating") or 0.0),
                votes=int(item.get("votes") or 0),
                source=self.name,
            )
            for item in data.get("results") or []
            if self._is_chord_sheet(item)
        ]
        # Most-voted first: usually the version everybody actually plays.
        return sorted(found, key=lambda r: r.votes, reverse=True)

    def _is_chord_sheet(self, item: dict) -> bool:
        """Skip the paid Pro entries -- they carry no sheet and would only error."""
        url = item.get("tab_url") or ""
        return (
            item.get("type") == "Chords"
            and urllib.parse.urlparse(url).hostname == _SHEET_HOST
        )

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
            site=self.name,
            body=self._clean(content),
        )

    def _clean(self, content: str) -> str:
        return _MARKERS.sub("", content).replace("\r\n", "\n").strip("\n")

    def _download(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
