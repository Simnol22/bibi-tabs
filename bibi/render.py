"""A song as a standalone HTML page.

Monospace and pre-formatted, because the whole point is that a chord sits over
the syllable it belongs to. Chord lines get colour; nothing gets re-flowed.
"""

from __future__ import annotations

import html
from pathlib import Path

from .song import Song

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
"""


class HtmlRenderer:
    def render(self, song: Song) -> str:
        return (
            "<!doctype html>\n"
            f'<html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(song.title)}</title><style>{_CSS}</style></head>"
            f"<body><header>{self._header(song)}</header>"
            f"<pre>{self._body(song)}</pre></body></html>\n"
        )

    def write(self, song: Song, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(song), encoding="utf-8")
        return path

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

    def _body(self, song: Song) -> str:
        rows = []
        for line in song.lines:
            text = html.escape(line.text)
            rows.append(f'<span class="c">{text}</span>' if line.is_chords else text)
        return "\n".join(rows)
