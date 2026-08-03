"""A song as a standalone HTML page.

Monospace and pre-formatted, because the whole point is that a chord sits over
the syllable it belongs to. Chord lines get colour; nothing gets re-flowed.
"""

from __future__ import annotations

import html
import re
import urllib.parse
from pathlib import Path  # noqa: TC003 - used in signatures at runtime

from .chords import (
    MAX_TRANSPOSE,
    Transposer,
    chord_in,
    transpose_key,
    unambiguous_chord,
)
from .diagram import HEIGHT, WIDTH, Diagrams
from .song import SearchResult, Song, looks_like_chords

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
/* No overflow container: it would clip the chord diagrams. Long lines scroll
   the page instead, which is what a monospace chord sheet wants anyway. */
pre { max-width:60rem; margin:0 auto; overflow:visible;
      font-family: ui-monospace, "SF Mono", Menlo, monospace;
      font-size:15px; line-height:1.5; white-space:pre; }
.c { color:var(--accent); font-weight:600; }
a { color:var(--accent); }
@media print { body { background:#fff; color:#000 } .c { color:#000; font-weight:700 } }

/* landing page */
.wrap { max-width:60rem; margin:0 auto; }
/* A <form> imposes no layout: the edit screen wraps the whole page in one,
   and a flex rule here laid nav, header and sheet out side by side. */
form { margin:0; }
.bar { display:flex; gap:.5rem; margin:1rem 0 2rem; }
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
li .rate { color:var(--muted); font-size:.85rem; white-space:nowrap; min-width:5.5rem;
           text-align:right; }
li .site { margin-left:auto; color:var(--muted); font-size:.7rem; letter-spacing:.03em;
           text-transform:uppercase; white-space:nowrap; opacity:.75; }
.empty { color:var(--muted); }
li.row { display:flex; align-items:center; border-bottom:1px solid #8882; }
li.row a { flex:1; border:0; }
.del { background:none; border:0; color:var(--muted); font-size:1.4rem;
       line-height:1; padding:.2rem .6rem; }
.del:hover { color:#d24; }

/* song page nav */
nav { display:flex; align-items:center; justify-content:space-between;
      gap:1rem; padding-bottom:1rem; }
nav a { text-decoration:none; }
.ok { color:var(--muted); font-size:.9rem; }

/* transposer */
.tr { display:flex; align-items:center; gap:.5rem; margin-top:.9rem;
      color:var(--muted); font-size:.85rem; }
.tr a { display:inline-block; min-width:2rem; text-align:center; padding:.25rem .5rem;
        border:1px solid #8883; border-radius:8px; text-decoration:none;
        font-size:1rem; line-height:1.1; }
.tr a:hover { border-color:var(--accent); }
.tr b { min-width:2.2rem; text-align:center; color:var(--fg); font-size:1rem; }
.tr .reset { min-width:0; font-size:.8rem; border:0; }
.meta s { opacity:.55; }
@media print { nav, .tr { display:none } }

/* auto-scroll -- fixed, because it is the one control you reach for while the
   page is already moving, and the header is long gone by then. */
.sc { position:fixed; right:1rem; bottom:1rem; z-index:20;
      display:flex; align-items:center; gap:.4rem;
      padding:.4rem .5rem; border-radius:12px; border:1px solid #8883;
      background:color-mix(in srgb, var(--bg) 88%, transparent);
      backdrop-filter:blur(6px); color:var(--muted); font-size:.85rem; }
.sc button { font:inherit; padding:.3rem .6rem; border-radius:8px;
             border:1px solid #8883; background:none; color:var(--fg); }
.sc button:hover { border-color:var(--accent); }
.sc .go { background:var(--accent); color:#fff; border-color:transparent; }
.sc .step { min-width:2rem; font-size:1rem; line-height:1.1; }
.sc b { min-width:1.3rem; text-align:center; color:var(--fg); font-size:1rem; }
@media print { .sc { display:none } }

/* chord diagrams -- hover on a pointer, tap or tab elsewhere. No JavaScript. */
.defs { display:none; }
.ch { position:relative; cursor:help; outline:none; }
.ch:hover, .ch:focus { text-decoration:underline dotted; }
.pop { display:none; position:absolute; top:1.7em; left:-.4em; z-index:9;
       background:var(--bg); border:1px solid #8884; border-radius:10px;
       padding:.5rem 1.6rem .35rem; box-shadow:0 6px 22px rgb(0 0 0 / .18);
       color:var(--fg); }
.ch:hover .pop, .ch:focus .pop, .ch:focus-within .pop { display:block; }
/* Bridges the gap under the chord, or the popup closes as you reach for it. */
.pop::before { content:''; position:absolute; left:0; right:0; top:-.8em; height:.8em; }
.pop svg { display:block; width:110px; height:auto; }
@media print { .pop { display:none !important } }

/* Voicings: a radio per shape, one pane visible. The arrows are <label>s, so
   picking one is a click with no script behind it -- and because they are also
   a radio group, the left and right keys step through them for free. */
.pop > input { position:absolute; opacity:0; width:1px; height:1px; margin:0; }
.pop > span { display:none; position:relative; }
.pop > span:only-of-type { display:block; }
.pop > input:nth-of-type(1):checked ~ span:nth-of-type(1),
.pop > input:nth-of-type(2):checked ~ span:nth-of-type(2),
.pop > input:nth-of-type(3):checked ~ span:nth-of-type(3),
.pop > input:nth-of-type(4):checked ~ span:nth-of-type(4),
.pop > input:nth-of-type(5):checked ~ span:nth-of-type(5),
.pop > input:nth-of-type(6):checked ~ span:nth-of-type(6),
.pop > input:nth-of-type(7):checked ~ span:nth-of-type(7) { display:block; }
/* The radios are invisible, so the popup carries the focus ring for them. */
.pop:has(input:focus-visible) { outline:2px solid var(--accent); outline-offset:2px; }
/* Previous, then next: the order is the meaning, so they carry no class. */
.pop label { position:absolute; top:50%; margin-top:-.9rem; width:1.4rem; height:1.8rem;
             display:flex; align-items:center; justify-content:center;
             cursor:pointer; opacity:.4; }
.pop label:hover { opacity:1; }
.pop label:first-of-type { left:-1.4rem; }
.pop label:last-of-type { right:-1.4rem; }
/* Drawn, not written: a character here would paste with the copied sheet. */
.pop label::before { content:''; width:.4rem; height:.4rem;
                     border-right:2px solid currentColor;
                     border-bottom:2px solid currentColor; transform:rotate(-45deg); }
.pop label:first-of-type::before { transform:rotate(135deg); }

/* editing -- fields share the monospace grid with the lyrics beneath them */
.lock { font-size:1.2rem; text-decoration:none; }
.edit { max-width:60rem; margin:0 auto;
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size:15px; line-height:1.5; }
.edit .lyr { white-space:pre; }
.chl { display:block; font:inherit; line-height:inherit; padding:0; margin:0;
       border:0; border-radius:0; background:transparent; color:var(--accent);
       font-weight:600; caret-color:var(--accent); }
.chl.lyr { color:var(--fg); font-weight:400; }
.chl:hover { background:color-mix(in srgb, var(--accent) 8%, transparent); }
.chl:focus { outline:0; background:color-mix(in srgb, var(--accent) 14%, transparent); }
.hint { color:var(--muted); font-size:.85rem; max-width:44rem; }
/* A token on a chord line that is not a chord: an annotation, or a typo. */
.nc { color:var(--muted); font-weight:400; }
"""

#: The only JavaScript in the program. Nothing else can move the viewport: CSS
#: can slide content upward, but then the sheet would crawl out from under its
#: own chord popups, and the speed could not answer while it played.
#:
#: Speed is a level, 1 to 10, kept in the browser so it carries between songs.
#: Position is tracked as a float and written with scrollTo -- scrollBy rounds,
#: and at five pixels a second the rounding is the whole movement.
_JS = """
(function () {
  var PER_LEVEL = 5, TOP = 10;          // pixels a second, at level 1
  var button = document.getElementById('scroll');
  var shown = document.getElementById('level');
  var level = Math.min(TOP, Math.max(1, +localStorage.getItem('bibi-scroll') || 2));
  var at = 0, last = 0, running = false;

  function step(now) {
    if (!running) return;
    // Somebody grabbed the scrollbar, or hit a key. Follow, do not fight.
    if (Math.abs(scrollY - at) > 2) at = scrollY;
    at += (now - last) * level * PER_LEVEL / 1000;
    last = now;
    scrollTo(0, at);
    if (at >= document.documentElement.scrollHeight - innerHeight) return run(false);
    requestAnimationFrame(step);
  }

  function run(wanted) {
    running = wanted;
    button.textContent = running ? '\\u23F8 Pause' : '\\u25B6 Scroll';
    button.classList.toggle('go', running);
    if (!running) return;
    at = scrollY;
    last = performance.now();
    requestAnimationFrame(step);
  }

  function nudge(by) {
    level = Math.min(TOP, Math.max(1, level + by));
    shown.textContent = level;
    localStorage.setItem('bibi-scroll', level);
  }

  button.onclick = function () { run(!running); };
  document.getElementById('slower').onclick = function () { nudge(-1); };
  document.getElementById('faster').onclick = function () { nudge(1); };
  nudge(0);
})();
"""


class HtmlRenderer:
    def render(
        self,
        song: Song,
        home: str | None = None,
        save_url: str | None = None,
        saved: bool = False,
        semitones: int = 0,
        transpose_url: str | None = None,
        edit_url: str | None = None,
    ) -> str:
        """A song page.

        `home` adds a back link -- omitted for the standalone file the CLI
        writes, where there is nowhere to go back to. `save_url` adds the save
        button, for a song that has been fetched but not kept yet. `semitones`
        shifts the chords for display only; the stored song never changes, and
        `transpose_url` is a `{t}` template for where the +/- buttons point.
        """
        body, defs = self._body(song, semitones)
        return (
            "<!doctype html>\n"
            f'<html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(song.title)}</title><style>{_CSS}</style></head>"
            f"<body>{self._nav(home, save_url, saved, edit_url)}"
            f"<header>{self._header(song, semitones)}"
            f"{self._transposer(transpose_url, semitones)}</header>"
            f"<pre>{body}</pre>{defs}{self._autoscroll()}"
            f"<script>{_JS}</script></body></html>\n"
        )

    def edit(self, song: Song) -> str:
        """The sheet with its chord lines editable, in place.

        Always the stored key: transposing is a display trick, and saving an
        edit made against a transposed view would silently re-key the song.

        Each chord line becomes a monospace field sitting exactly where it was,
        with its lyric static underneath. Spaces move a chord, deleting the
        token removes it, typing adds one -- and every lyric line without
        chords gets an empty field, so you can add where there was nothing.
        """
        lines = song.body.split("\n")
        # In `ch` units a monospace column is exactly one character, so the
        # field and the lyric below it share a grid.
        width = max((len(line) for line in lines), default=40) + 8

        rows = []
        for i, line in enumerate(lines):
            if line.strip() == "":
                rows.append('<div class="lyr">&nbsp;</div>')
                continue
            chords = looks_like_chords(line)
            if not chords and (i == 0 or not looks_like_chords(lines[i - 1])):
                # An empty field only where there is no chord line already, or
                # every lyric would be pushed a row away from its own chords.
                rows.append(self._chord_field(f"n{i}", "", width))
            rows.append(self._chord_field(f"l{i}", line, width, chords))

        return (
            "<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(song.title)}</title><style>{_CSS}</style></head>"
            '<body><form method="post" action="/edit">'
            f'<input type="hidden" name="slug" value="{html.escape(song.slug)}">'
            '<nav class="wrap">'
            f'<a href="/song/{html.escape(song.slug)}">Cancel</a>'
            "<button>&#128274; Lock and save</button></nav>"
            f"<header>{self._header(song)}"
            '<p class="hint">Editing the chords only, in the key the song is '
            "stored in. Move one with spaces, clear it to delete it, or type "
            "into an empty line to add one.</p></header>"
            f'<div class="edit">{"".join(rows)}</div>'
            "</form></body></html>\n"
        )

    def _chord_field(self, name: str, value: str, width: int, chords: bool = True) -> str:
        """A line as an editable field. Chord lines are coloured, lyrics are not."""
        return (
            f'<input class="chl{"" if chords else " lyr"}" name="{name}" '
            f'value="{html.escape(value)}" spellcheck="false" '
            f'autocapitalize="off" autocomplete="off" style="width:{width}ch">'
        )

    def _transposer(self, url: str | None, semitones: int) -> str:
        """Plain links: transposing changes nothing on disk, so GET is right.

        `url` is a `{t}` template, absent for the CLI's standalone file where
        there is no server to ask for another rendering.
        """
        if url is None:
            return ""
        down = max(-MAX_TRANSPOSE, semitones - 1)
        up = min(MAX_TRANSPOSE, semitones + 1)
        showing = f"+{semitones}" if semitones > 0 else str(semitones)
        reset = f'<a class="reset" href="{url.format(t=0)}">reset</a>' if semitones else ""
        return (
            '<div class="tr"><span>Transpose</span>'
            f'<a href="{url.format(t=down)}" aria-label="Down a semitone">&minus;</a>'
            f"<b>{showing}</b>"
            f'<a href="{url.format(t=up)}" aria-label="Up a semitone">+</a>'
            f"{reset}</div>"
        )

    def _autoscroll(self) -> str:
        """Play/pause and a speed level, sitting above the sheet.

        Buttons rather than links: transposing asks the server for another
        rendering, but changing speed mid-song must not reload the page and
        throw you back to the top. The level shown here is a placeholder --
        the script fills it in from whatever was last chosen.
        """
        return (
            '<div class="sc">'
            '<button type="button" id="scroll">&#9654; Scroll</button>'
            '<button type="button" class="step" id="slower" '
            'aria-label="Slower">&minus;</button>'
            '<b id="level">2</b>'
            '<button type="button" class="step" id="faster" '
            'aria-label="Faster">+</button>'
            "</div>"
        )

    def write(self, song: Song, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(song), encoding="utf-8")
        return path

    def _nav(
        self,
        home: str | None,
        save_url: str | None,
        saved: bool,
        edit_url: str | None = None,
    ) -> str:
        if home is None and save_url is None and not saved:
            return ""
        left = f'<a href="{home}">&larr; Library</a>' if home else "<span></span>"

        if save_url:
            right = (
                '<form method="post" action="/save">'
                f'<input type="hidden" name="url" value="{html.escape(save_url)}">'
                "<button>Save to library</button></form>"
            )
        elif edit_url:
            right = (
                f'<a class="lock" href="{edit_url}" title="Unlock to edit chords">'
                "&#128274;</a>"
            )
        elif saved:
            right = '<span class="ok">Saved</span>'
        else:
            right = ""
        return f'<nav class="wrap">{left}{right}</nav>'

    def _header(self, song: Song, semitones: int = 0) -> str:
        parts = [f"<h1>{html.escape(song.title)}</h1>"]
        if song.artist:
            parts.append(f'<div class="by">{html.escape(song.artist)}</div>')

        meta = []
        if song.capo:
            meta.append(f"<span><b>Capo {song.capo}</b></span>")
        if song.key:
            showing = transpose_key(song.key, semitones)
            was = f" <s>{html.escape(song.key)}</s>" if showing != song.key else ""
            meta.append(f"<span>Key {html.escape(showing)}{was}</span>")
        if song.source:
            where = html.escape(song.site) if song.site else "source"
            meta.append(f'<a href="{html.escape(song.source)}">{where}</a>')
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
            '<form class="bar" action="/search" method="get">'
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
            '<form class="bar" method="post" action="/settings">'
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
            votes = f"{item.rating:.1f} · {item.votes:,}" if item.votes else ""
            version = f"v{item.version}" if item.version else ""
            site = f'<span class="site">{html.escape(item.source)}</span>' if item.source else ""
            rows.append(
                f'<li><a href="{link}"><span>{html.escape(item.title)}</span>'
                f'<span class="who">{html.escape(item.artist)} {version}</span>'
                f'{site}<span class="rate">{votes}</span></a></li>'
            )
        return f"<ul>{''.join(rows)}</ul>"

    def _saved(self, saved: list[Song]) -> str:
        if not saved:
            return '<p class="empty">Nothing saved yet — search for something.</p>'
        rows = []
        for song in saved:
            capo = f"capo {song.capo}" if song.capo else ""
            label = html.escape(f"{song.title} — {song.artist}" if song.artist else song.title)
            site = f'<span class="site">{html.escape(song.site)}</span>' if song.site else ""
            rows.append(
                f'<li class="row"><a href="/song/{song.slug}">'
                f"<span>{html.escape(song.title)}</span>"
                f'<span class="who">{html.escape(song.artist)}</span>'
                f'{site}<span class="rate">{capo}</span></a>'
                # POST, not a link: a GET that deletes gets fired by browser
                # prefetch and by going back in history.
                f'<form method="post" action="/delete" '
                f"onsubmit=\"return confirm('Remove {label}?')\">"
                f'<input type="hidden" name="slug" value="{song.slug}">'
                f'<button class="del" title="Remove">&times;</button></form></li>'
            )
        return f"<ul>{''.join(rows)}</ul>"

    def _body(self, song: Song, semitones: int = 0) -> tuple[str, str]:
        """The sheet, plus the diagram definitions it refers to."""
        transposer = Transposer.for_song(song.key, song.body, semitones)
        diagrams = Diagrams()
        rows = []
        for line in song.lines:
            if line.is_chords:
                shifted = transposer.line(line.text)
                rows.append(f'<span class="c">{self._chords(shifted, diagrams)}</span>')
            else:
                rows.append(self._stray_chords(line.text, transposer, diagrams))
        return "\n".join(rows), diagrams.defs()

    def _stray_chords(self, line: str, transposer: Transposer, diagrams: Diagrams) -> str:
        """Colour a chord standing among words, on a line that is not a chord line.

        Real sheets put chords in intro notes and annotations, where the line
        never reaches the 80% threshold. Only unmistakable spellings qualify --
        a lone `A` is a word far more often than a chord. These shift with the
        transposition like any other chord, or they would go stale.
        """
        return self._tokens(line, diagrams, lambda t: unambiguous_chord(t) is not None,
                            transposer, plain_is_muted=False)

    def _chords(self, line: str, diagrams: Diagrams) -> str:
        """Wrap each chord so it can show its shape, leaving columns untouched.

        The spans add no characters, and the popup is absolutely positioned, so
        the alignment inside <pre> is exactly as it was.
        """
        return self._tokens(line, diagrams, lambda t: True, None, plain_is_muted=True)

    def _popup(self, refs: tuple[str, ...], group: str) -> str:
        """Every known voicing of one chord, one visible at a time.

        A radio per voicing and a pair of <label> arrows per pane: checking a
        radio swaps the pane, which is a carousel with no JavaScript in it. The
        arrows wrap around, so neither one is ever a dead end.

        Nothing here may be selectable text. The popup sits inside the <pre>,
        so a stray character would paste when the sheet is copied -- the arrows
        are drawn in CSS from an empty element, and the "2 of 4" counter lives
        inside the SVG symbol where selection cannot reach it.
        """
        if len(refs) == 1:
            return (
                f'<span class="pop"><span><svg viewBox="0 0 {WIDTH} {HEIGHT}">'
                f'<use href="#{refs[0]}"/></svg></span></span>'
            )

        last = len(refs) - 1
        radios = "".join(
            f'<input type="radio" name="{group}" id="{group}-{i}"'
            f'{" checked" if i == 0 else ""}>'
            for i in range(len(refs))
        )
        # The two labels are always previous then next, so their order carries
        # the meaning and they need no class of their own -- worth 15 KB on a
        # sheet with a hundred chords in it.
        panes = "".join(
            f'<span><svg viewBox="0 0 {WIDTH} {HEIGHT}"><use href="#{ref}"/></svg>'
            f'<label for="{group}-{i - 1 if i else last}"></label>'
            f'<label for="{group}-{0 if i == last else i + 1}"></label>'
            "</span>"
            for i, ref in enumerate(refs)
        )
        return f'<span class="pop">{radios}{panes}</span>'

    def _tokens(self, line, diagrams, wanted, transposer, plain_is_muted):  # noqa: ANN001
        out = []
        cursor = 0
        for match in re.finditer(r"\S+", line):
            out.append(html.escape(line[cursor : match.start()]))
            token = match.group()
            cursor = match.end()

            if not wanted(token):
                out.append(html.escape(token))
                continue
            if transposer is not None:
                token = transposer.token(token)
            if chord_in(token) is None:
                # Not a chord: an annotation like "x4", or a typo made while
                # editing. Muted, so a mistake is visible once locked.
                out.append(
                    f'<span class="nc">{html.escape(token)}</span>'
                    if plain_is_muted
                    else html.escape(token)
                )
                continue

            refs = diagrams.add(token)
            if not refs:
                out.append(html.escape(token))
            else:
                # tabindex makes it work on touch, where there is no hover.
                # No caption inside the popup: it would be a second copy of the
                # chord name in the <pre>, so copying the sheet would paste
                # every chord twice.
                out.append(
                    f'<span class="ch" tabindex="0">{html.escape(token)}'
                    f"{self._popup(refs, diagrams.next_group())}</span>"
                )
        out.append(html.escape(line[cursor:]))
        return "".join(out)

