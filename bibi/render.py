"""A song as a standalone HTML page.

Monospace and pre-formatted, because the whole point is that a chord sits over
the syllable it belongs to. Chord lines get colour; nothing gets re-flowed.
"""

from __future__ import annotations

import html
import urllib.parse
from pathlib import Path  # noqa: TC003 - used in signatures at runtime

from .song import SearchResult, Song

_CSS = """
:root { color-scheme: light dark;
        --bg:#fbfaf8; --fg:#1b1d22; --muted:#6d6a64; --accent:#c05621; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#181a20; --fg:#f0eee9; --muted:#9a9790; --accent:#e87a41; } }
* { box-sizing: border-box }
body { margin:0; padding:1.5rem 1.25rem 4rem; background:var(--bg); color:var(--fg);
       font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; }
header { max-width:60rem; margin:0 auto 1.25rem; }
h1 { margin:0; font-size:1.4rem; }
.by { color:var(--muted); }
.meta { margin-top:.5rem; display:flex; gap:1rem; flex-wrap:wrap;
        color:var(--muted); font-size:.85rem; }
.meta b { color:var(--accent); }
pre { max-width:60rem; margin:0 auto; overflow-x:auto;
      font-family: ui-monospace, "SF Mono", Menlo, monospace;
      font-size:15px; line-height:1.5; white-space:pre; }
.c { color:var(--accent); font-weight:600; }
a { color:var(--accent); }
@media print { body { background:#fff; color:#000 } .c { color:#000; font-weight:700 } }

/* landing page */
.wrap { max-width:60rem; margin:0 auto; }
form { display:flex; gap:.5rem; margin:1rem 0 2rem; }
input[type=search] { flex:1; font:inherit; padding:.6rem .8rem; border-radius:8px;
  border:1px solid #8883; background:var(--bg); color:var(--fg); }
button { font:inherit; padding:.6rem 1rem; border-radius:8px; border:1px solid #8883;
  background:var(--accent); color:#fff; cursor:pointer; }
h2 { font-size:.8rem; text-transform:uppercase; letter-spacing:.06em;
     color:var(--muted); margin:2rem 0 .5rem; }
ul { list-style:none; padding:0; margin:0; }
li a { display:flex; align-items:baseline; gap:.6rem; padding:.6rem .3rem;
       border-bottom:1px solid #8882; text-decoration:none; color:var(--fg); }
li a:hover { color:var(--accent); }
li .who { color:var(--muted); font-size:.9rem; }
li .rate { margin-left:auto; color:var(--muted); font-size:.85rem; white-space:nowrap; }
.empty { color:var(--muted); }
li.row { display:flex; align-items:center; border-bottom:1px solid #8882; }
li.row a { flex:1; border:0; }
li.row form { margin:0; }
.del { background:none; border:0; color:var(--muted); font-size:1.4rem;
       line-height:1; padding:.2rem .6rem; }
.del:hover { color:#d24; }

/* song page nav */
nav { display:flex; align-items:center; justify-content:space-between;
      gap:1rem; padding-bottom:1rem; }
nav form { margin:0; }
nav a { text-decoration:none; }
.ok { color:var(--muted); font-size:.9rem; }
@media print { nav { display:none } }
"""


class HtmlRenderer:
    def render(
        self,
        song: Song,
        home: str | None = None,
        save_url: str | None = None,
        saved: bool = False,
    ) -> str:
        """A song page.

        `home` adds a back link -- omitted for the standalone file the CLI
        writes, where there is nowhere to go back to. `save_url` adds the save
        button, for a song that has been fetched but not kept yet.
        """
        return (
            "<!doctype html>\n"
            f'<html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(song.title)}</title><style>{_CSS}</style></head>"
            f"<body>{self._nav(home, save_url, saved)}"
            f"<header>{self._header(song)}</header>"
            f"<pre>{self._body(song)}</pre></body></html>\n"
        )

    def write(self, song: Song, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(song), encoding="utf-8")
        return path

    def _nav(self, home: str | None, save_url: str | None, saved: bool) -> str:
        if home is None and save_url is None and not saved:
            return ""
        left = f'<a href="{home}">&larr; Library</a>' if home else "<span></span>"

        if save_url:
            right = (
                '<form method="post" action="/save">'
                f'<input type="hidden" name="url" value="{html.escape(save_url)}">'
                "<button>Save to library</button></form>"
            )
        elif saved:
            right = '<span class="ok">Saved</span>'
        else:
            right = ""
        return f'<nav class="wrap">{left}{right}</nav>'

    def _header(self, song: Song) -> str:
        parts = [f"<h1>{html.escape(song.title)}</h1>"]
        if song.artist:
            parts.append(f'<div class="by">{html.escape(song.artist)}</div>')

        meta = []
        if song.capo:
            meta.append(f"<span><b>Capo {song.capo}</b></span>")
        if song.key:
            meta.append(f"<span>Key {html.escape(song.key)}</span>")
        if song.source:
            meta.append(f'<a href="{html.escape(song.source)}">source</a>')
        if meta:
            parts.append(f'<div class="meta">{"".join(meta)}</div>')
        return "".join(parts)

    def index(
        self,
        saved: list[Song],
        query: str = "",
        results: list[SearchResult] | None = None,
    ) -> str:
        """The landing page: search on top, your library underneath."""
        sections = ""
        if results is not None:
            sections += f"<h2>Results for “{html.escape(query)}”</h2>"
            sections += self._results(results)
        sections += "<h2>Saved</h2>" + self._saved(saved)

        return (
            "<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>BIBI-tabs</title><style>{_CSS}</style></head>"
            '<body><div class="wrap">'
            '<nav><h1>BIBI-tabs</h1><a href="/settings">Settings</a></nav>'
            '<form action="/search" method="get">'
            f'<input type="search" name="q" placeholder="Search a song" '
            f'value="{html.escape(query)}" autofocus>'
            "<button>Search</button></form>"
            f"{sections}</div></body></html>\n"
        )

    def settings(self, library: Path, message: str = "") -> str:
        note = f'<p class="ok">{html.escape(message)}</p>' if message else ""
        return (
            "<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>Settings</title><style>{_CSS}</style></head>"
            '<body><div class="wrap">'
            '<nav><a href="/">&larr; Library</a></nav>'
            "<h1>Settings</h1>"
            f"{note}"
            '<h2>Where songs are kept</h2>'
            '<form method="post" action="/settings">'
            f'<input type="text" name="library" value="{html.escape(str(library))}">'
            "<button>Save</button></form>"
            '<p class="empty">Songs move with the folder. They stay plain text '
            "either way, so they are readable without this program.<br>"
            "Keeping them outside a git repository is wise — they are copyrighted."
            "</p></div></body></html>\n"
        )

    def _results(self, results: list[SearchResult]) -> str:
        if not results:
            return '<p class="empty">Nothing found. Try just the song title.</p>'
        rows = []
        for item in results:
            link = f"/view?url={urllib.parse.quote(item.url, safe='')}"
            votes = f"{item.rating:.1f} · {item.votes:,}" if item.votes else "unrated"
            version = f"v{item.version}" if item.version else ""
            rows.append(
                f'<li><a href="{link}"><span>{html.escape(item.title)}</span>'
                f'<span class="who">{html.escape(item.artist)} {version}</span>'
                f'<span class="rate">{votes}</span></a></li>'
            )
        return f"<ul>{''.join(rows)}</ul>"

    def _saved(self, saved: list[Song]) -> str:
        if not saved:
            return '<p class="empty">Nothing saved yet — search for something.</p>'
        rows = []
        for song in saved:
            capo = f"capo {song.capo}" if song.capo else ""
            label = html.escape(f"{song.title} — {song.artist}" if song.artist else song.title)
            rows.append(
                f'<li class="row"><a href="/song/{song.slug}">'
                f"<span>{html.escape(song.title)}</span>"
                f'<span class="who">{html.escape(song.artist)}</span>'
                f'<span class="rate">{capo}</span></a>'
                # POST, not a link: a GET that deletes gets fired by browser
                # prefetch and by going back in history.
                f'<form method="post" action="/delete" '
                f"onsubmit=\"return confirm('Remove {label}?')\">"
                f'<input type="hidden" name="slug" value="{song.slug}">'
                f'<button class="del" title="Remove">&times;</button></form></li>'
            )
        return f"<ul>{''.join(rows)}</ul>"

    def _body(self, song: Song) -> str:
        rows = []
        for line in song.lines:
            text = html.escape(line.text)
            rows.append(f'<span class="c">{text}</span>' if line.is_chords else text)
        return "\n".join(rows)
