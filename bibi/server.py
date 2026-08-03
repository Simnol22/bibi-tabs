"""A small local web app: search, fetch, read.

Bound to 127.0.0.1 only. It exists so a browser page can trigger a fetch --
Ultimate Guitar cannot be read from JavaScript, which is the whole reason this
program is Python rather than a web app.

The page-building methods return strings and touch no sockets, so they are
testable without starting anything.
"""

from __future__ import annotations

import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .chords import MAX_TRANSPOSE
from .config import Config
from .library import Library
from .render import HtmlRenderer
from .song import Song
from .sources import Sources
from .ultimate_guitar import NotAChordPage

DEFAULT_PORT = 8777
#: How many fetched songs to keep, so transposing a preview costs nothing.
RECENT_LIMIT = 8


def _semitones(raw: str) -> int:
    """A hand-edited ?t= should not be able to 500 the page."""
    try:
        return int(raw)
    except ValueError:
        return 0


def _clamp(semitones: int) -> int:
    return max(-MAX_TRANSPOSE, min(MAX_TRANSPOSE, semitones))


class Server:
    def __init__(
        self,
        library: Library | None = None,
        source: Sources | None = None,
        renderer: HtmlRenderer | None = None,
        port: int = DEFAULT_PORT,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.library = library or Library(home=self.config.library)
        self.source = source or Sources()
        self.renderer = renderer or HtmlRenderer()
        self.port = port
        self._recent: dict[str, Song] = {}

    # --- pages -----------------------------------------------------------

    def index_page(self) -> str:
        return self.renderer.index(self._saved())

    def search_page(self, query: str) -> str:
        if not query.strip():
            return self.index_page()
        try:
            results = self.source.search(query)
        except (NotAChordPage, OSError):
            results = []
        return self.renderer.index(self._saved(), query, results)

    def song_page(self, slug: str, semitones: int = 0) -> str | None:
        path = self.library.path_for_slug(slug)
        if path is None:
            return None
        return self.renderer.render(
            self.library.load(path),
            home="/",
            saved=True,
            semitones=_clamp(semitones),
            transpose_url=f"/song/{urllib.parse.quote(slug)}?t={{t}}",
        )

    def view_page(self, url: str, semitones: int = 0) -> str:
        """Read a song without keeping it. Opening is not the same as wanting."""
        song = self._fetch(url)
        already = self.library.path_for_slug(song.slug) is not None
        quoted = urllib.parse.quote(url, safe="")
        return self.renderer.render(
            song,
            home="/",
            save_url=None if already else url,
            saved=already,
            semitones=_clamp(semitones),
            transpose_url=f"/view?url={quoted}&t={{t}}",
        )

    def save(self, url: str) -> str:
        """Fetch and keep, returning the slug to redirect to."""
        song = self._fetch(url)
        self.library.save(song)
        return song.slug

    def delete(self, slug: str) -> None:
        self.library.delete(slug)

    def settings_page(self, message: str = "") -> str:
        return self.renderer.settings(self.library.home, message)

    def set_library(self, raw: str) -> str:
        """Point the library somewhere else, taking the songs along."""
        wanted = Path(raw.strip()).expanduser()
        if not raw.strip() or not wanted.is_absolute():
            return self.settings_page("Give a full path, starting from / or ~.")
        try:
            moved = self.library.move_to(wanted)
        except OSError as error:
            return self.settings_page(f"Couldn't use that folder: {error}")

        self.config.set_library(wanted)
        self.library = Library(home=wanted)
        songs = f"{moved} song{'s' if moved != 1 else ''} moved. " if moved else ""
        return self.settings_page(f"{songs}Songs are now kept in {wanted}.")

    def _fetch(self, url: str) -> Song:
        """Every outbound request goes through here.

        The host is checked first: these endpoints live on localhost, so any
        page open in the browser can aim one somewhere of its choosing.

        The last few songs are kept so that transposing a preview -- which
        reloads the page on every click -- does not hammer Ultimate Guitar.
        """
        if not self.source.matches(url):
            raise NotAChordPage("not an Ultimate Guitar url")
        if url in self._recent:
            return self._recent[url]

        song = self.source.fetch(url)
        self._recent[url] = song
        while len(self._recent) > RECENT_LIMIT:
            self._recent.pop(next(iter(self._recent)))
        return song

    def _saved(self) -> list[Song]:
        return [self.library.load(path) for path in self.library.paths()]

    # --- serving ---------------------------------------------------------

    def serve(self, open_browser: bool = True) -> int:
        httpd = ThreadingHTTPServer(("127.0.0.1", self.port), _Handler)
        httpd.app = self  # type: ignore[attr-defined]
        url = f"http://localhost:{self.port}/"
        print(f"BIBI-tabs on {url}   (ctrl-c to stop)")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
        finally:
            httpd.server_close()
        return 0


class _Handler(BaseHTTPRequestHandler):
    server_version = "bibi"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        app: Server = self.server.app  # type: ignore[attr-defined]
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/":
            self._html(app.index_page())
        elif parsed.path == "/search":
            self._html(app.search_page(query.get("q", [""])[0]))
        elif parsed.path == "/view":
            self._fetching(
                lambda: self._html(
                    app.view_page(
                        query.get("url", [""])[0], _semitones(query.get("t", ["0"])[0])
                    )
                )
            )
        elif parsed.path == "/settings":
            self._html(app.settings_page())
        elif parsed.path.startswith("/song/"):
            slug = urllib.parse.unquote(parsed.path[len("/song/") :])
            page = app.song_page(slug, _semitones(query.get("t", ["0"])[0]))
            self._html(page) if page else self._oops(404, "No such song.")
        else:
            self._oops(404, "Nothing here.")

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        """Saving and deleting change things, so they are never a GET."""
        app: Server = self.server.app  # type: ignore[attr-defined]
        path = urllib.parse.urlparse(self.path).path
        form = self._form()

        if path == "/save":
            self._fetching(
                lambda: self._see_other(f"/song/{urllib.parse.quote(app.save(form.get('url', [''])[0]))}")
            )
        elif path == "/delete":
            app.delete(form.get("slug", [""])[0])
            self._see_other("/")
        elif path == "/settings":
            self._html(app.set_library(form.get("library", [""])[0]))
        else:
            self._oops(404, "Nothing here.")

    def _form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length") or 0)
        return urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))

    def _fetching(self, action) -> None:  # noqa: ANN001
        """Anything that reaches out can fail in exactly two ways."""
        try:
            action()
        except NotAChordPage as error:
            self._oops(400, f"Couldn't read that one: {error}")
        except OSError as error:
            self._oops(502, f"Couldn't reach Ultimate Guitar: {error}")

    def _see_other(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def _html(self, body: str, status: int = 200) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _oops(self, status: int, message: str) -> None:
        import html as _html

        self._html(
            f"<!doctype html><meta charset=utf-8><title>{status}</title>"
            f'<body style="font-family:system-ui;padding:2rem">'
            f"<p>{_html.escape(message)}</p><p><a href='/'>Back</a></p>",
            status,
        )

    def log_message(self, *args: object) -> None:
        """Quiet. The browser is the interface, not the terminal."""
