"""bibi -- open a chord sheet.

    bibi                         open the app: search, and your saved songs
    bibi <ultimate-guitar-url>   fetch it, keep it, open it
    bibi <words>                 open something already saved
    bibi --list                  what's saved, in the terminal
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import webbrowser
from pathlib import Path

from .library import Library
from .render import HtmlRenderer
from .server import DEFAULT_PORT, Server
from .song import Song
from .ultimate_guitar import NotAChordPage, UltimateGuitar


class App:
    def __init__(self, library: Library | None = None) -> None:
        self.library = library or Library()
        self.source = UltimateGuitar()
        self.renderer = HtmlRenderer()

    def run(self, argv: list[str]) -> int:
        parser = argparse.ArgumentParser(
            prog="bibi",
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument("target", nargs="?", help="a UG url, or words from a saved song")
        parser.add_argument("-l", "--list", action="store_true", help="list saved songs")
        parser.add_argument("--no-open", action="store_true", help="don't launch a browser")
        parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="port for the app")
        args = parser.parse_args(argv)

        if args.list:
            return self.show_library()
        if not args.target:
            return Server(self.library, self.source, self.renderer, args.port).serve(
                open_browser=not args.no_open
            )
        if self.source.matches(args.target):
            return self.add(args.target, open_it=not args.no_open)
        return self.open_saved(args.target, open_it=not args.no_open)

    def show_library(self) -> int:
        paths = self.library.paths()
        if not paths:
            print("Nothing saved yet. Give me an Ultimate Guitar link.")
            return 0
        print(f"{len(paths)} song(s) in {self.library.home}\n")
        for path in paths:
            print(f"  {path.stem}")
        return 0

    def add(self, url: str, open_it: bool = True) -> int:
        try:
            song = self.source.fetch(url)
        except NotAChordPage as error:
            print(f"Couldn't read that page: {error}", file=sys.stderr)
            return 1
        except OSError as error:
            print(f"Couldn't reach Ultimate Guitar: {error}", file=sys.stderr)
            return 1

        saved = self.library.save(song)
        print(f"{song.title} — {song.artist}" if song.artist else song.title)
        print(f"saved  {saved}")
        return self.display(song, open_it)

    def open_saved(self, query: str, open_it: bool = True) -> int:
        path = self.library.find(query)
        if path is None:
            print(f"Nothing saved matching “{query}”.", file=sys.stderr)
            return 1
        return self.display(self.library.load(path), open_it)

    def display(self, song: Song, open_it: bool) -> int:
        page = Path(tempfile.gettempdir()) / f"bibi-{song.slug}.html"
        self.renderer.write(song, page)
        print(f"open   {page}")
        if open_it:
            webbrowser.open(page.as_uri())
        return 0


def main() -> int:
    return App().run(sys.argv[1:])
