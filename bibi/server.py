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

from .library import Library
from .render import HtmlRenderer
from .song import Song
from .ultimate_guitar import NotAChordPage, UltimateGuitar

DEFAULT_PORT = 8777


class Server:
    def __init__(
        self,
        library: Library | None = None,
        source: UltimateGuitar | None = None,
        renderer: HtmlRenderer | None = None,
        port: int = DEFAULT_PORT,
    ) -> None:
        self.library = library or Library()
        self.source = source or UltimateGuitar()
        self.renderer = renderer or HtmlRenderer()
        self.port = port

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

    def song_page(self, slug: str) -> str | None:
        path = self.library.path_for_slug(slug)
        return None if path is None else self.renderer.render(self.library.load(path))

    def add(self, url: str) -> str:
        """Fetch and save, returning the slug to redirect to.

        matches() is checked before any request goes out: this endpoint is a
        GET on localhost, so any page in the browser can aim it somewhere.
        """
        if not self.source.matches(url):
            raise NotAChordPage("not an Ultimate Guitar url")
        song = self.source.fetch(url)
        self.library.save(song)
        return song.slug

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
        elif parsed.path == "/add":
            self._add(app, query.get("url", [""])[0])
        elif parsed.path.startswith("/song/"):
            slug = urllib.parse.unquote(parsed.path[len("/song/") :])
            page = app.song_page(slug)
            self._html(page) if page else self._oops(404, "No such song.")
        else:
            self._oops(404, "Nothing here.")

    def _add(self, app: Server, url: str) -> None:
        try:
            slug = app.add(url)
        except NotAChordPage as error:
            self._oops(400, f"Couldn't read that one: {error}")
        except OSError as error:
            self._oops(502, f"Couldn't reach Ultimate Guitar: {error}")
        else:
            self.send_response(303)
            self.send_header("Location", f"/song/{urllib.parse.quote(slug)}")
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
