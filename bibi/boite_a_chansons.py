"""Reading a song off boiteachansons.net.

Everything site-specific lives here, same as ultimate_guitar.py.

Their format is the mirror image of UG's. Rather than pre-aligned text with
markers laid over it, chords are anchored *inline*:

    <div class="pL"><span class="sI"><span class="a" data-a="Em"></span>text…

So the columns are not given -- they have to be built, by noting how much lyric
has accumulated when each chord appears. That is what lay_out does.
"""

from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from .chords import lay_out
from .song import SearchResult, Song
from .ultimate_guitar import NotAChordPage

_HOST = "boiteachansons.net"
_SEARCH = "https://www.boiteachansons.net/recherche/"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
#: A song link, as opposed to the menu links that share the /partitions/ prefix.
_RESULT = re.compile(
    r'href="(https://www\.boiteachansons\.net/partitions/[^"/?#]+/[^"/?#]+)"'
    r'[^>]*?title="([^"]*)"'
)
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
          "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}


class _SheetParser(HTMLParser):
    """Pulls the sheet out of <div id="divPartition">.

    There are two such containers -- a hidden "perso" one for user edits comes
    first -- so only the one with the right id is read.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._depth = 0  # div nesting inside the sheet, 0 when outside
        self._line: list[str] = []
        self._chords: list[tuple[int, str]] = []
        self._in_line = False
        self._label = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        got = dict(attrs)
        classes = (got.get("class") or "").split()

        if tag == "div" and got.get("id") == "divPartition":
            self._depth = 1
            return
        if not self._depth:
            return
        if tag == "div":
            self._depth += 1
            if "pL" in classes:
                self._in_line, self._line, self._chords = True, [], []
            elif "pLS" in classes:
                self._label = True
        elif tag == "span" and "a" in classes and got.get("data-a"):
            # An empty span whose chord belongs above the text that follows it.
            self._chords.append((sum(len(p) for p in self._line), got["data-a"]))

    def handle_data(self, data: str) -> None:
        if self._depth and (self._in_line or self._label):
            self._line.append(data.replace("\xa0", " "))

    def handle_endtag(self, tag: str) -> None:
        if tag != "div" or not self._depth:
            return
        self._depth -= 1
        if self._depth == 0:
            return
        if self._label:
            self._flush_label()
        elif self._in_line:
            self._flush_line()

    def _flush_label(self) -> None:
        text = "".join(self._line).strip()
        if text:
            self.lines.extend(["", text])
        self._label, self._line = False, []

    def _flush_line(self) -> None:
        lyric = "".join(self._line).rstrip()
        if self._chords:
            self.lines.append(lay_out(self._chords))
        self.lines.append(lyric)
        self._in_line, self._line, self._chords = False, [], []


class BoiteAChansons:
    """Fetches a boiteachansons.net page and turns it into a Song."""

    name = "Boîte à Chansons"

    def matches(self, url: str) -> bool:
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
            raise NotAChordPage(f"not a Boîte à Chansons url: {url}")
        return self.parse(self._download(url), url)

    def parse(self, page: str, url: str = "") -> Song:
        parser = _SheetParser()
        parser.feed(page)
        body = "\n".join(parser.lines).strip("\n")
        if not body:
            raise NotAChordPage("no sheet on that page -- the layout may have changed")

        title, artist = self._titles(page)
        return Song(
            title=title,
            artist=artist,
            capo=self._capo(page),
            key=self._field(page, "tonalite"),
            source=url,
            site=self.name,
            body=body,
        )

    def search(self, query: str) -> list[SearchResult]:
        """Their search is a POST, unlike UG's."""
        data = urllib.parse.urlencode({"inpRecherche": query}).encode()
        return self._results(self._download(_SEARCH, data))

    def _results(self, page: str) -> list[SearchResult]:
        """Results carry their own metadata in the link's title attribute.

        Two path segments after /partitions/ is what separates a song from the
        menu links (nouveautes, top50Chansons, aleatoire) that share the prefix.
        """
        found: list[SearchResult] = []
        seen: set[str] = set()
        for url, label in _RESULT.findall(page):
            if url in seen:
                continue
            seen.add(url)
            title, artist = self._split_label(label)
            if title:
                found.append(
                    SearchResult(title=title, artist=artist, url=url, source=self.name)
                )
        return found

    def _split_label(self, label: str) -> tuple[str, str]:
        """`Song - Artist - Paroles et accords` -> (song, artist)."""
        text = html.unescape(label).strip()
        text = re.sub(r"\s*-\s*Paroles et accords\s*$", "", text)
        title, _, artist = text.rpartition(" - ")
        return (title.strip(), artist.strip()) if title else (artist.strip(), "")

    def _titles(self, page: str) -> tuple[str, str]:
        """og:title reads "Song (Artist) - Paroles et accords - …"."""
        match = re.search(r'property="og:title"\s+content="([^"]+)"', page)
        raw = html.unescape(match.group(1)) if match else ""
        head = raw.split(" - ")[0].strip()
        paren = re.match(r"^(.*?)\s*\((.*)\)$", head)
        if paren:
            return paren.group(1).strip(), paren.group(2).strip()
        return head or "Untitled", ""

    def _capo(self, page: str) -> int:
        """They write it in Roman numerals: "Capo I"."""
        value = self._field(page, "capo")
        return _ROMAN.get(value.upper(), 0)

    def _field(self, page: str, name: str) -> str:
        match = re.search(rf'id="{name}"[^>]*value="([^"]*)"', page)
        return html.unescape(match.group(1)).strip() if match else ""

    def _download(self, url: str, data: bytes | None = None) -> str:
        request = urllib.request.Request(url, data=data, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
