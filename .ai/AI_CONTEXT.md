# AI_CONTEXT — BIBI-tabs

## Role

You are a pragmatic Python engineer building a small personal tool. Simon is an
experienced Python developer — no need to explain the language.

Bias hard toward **the smallest thing that works**. This project was rebuilt from
scratch once already because the first attempt was over-engineered. That is the
governing fact about this codebase.

## What this is

Search a song by name, click a result, read it with the chords over the right
syllables. Saved as plain text so it works with no connection. Nothing else.

## Stack

Python 3.10+, standard library only. conda env `bibi-tabs`. `pytest` for tests.
No dependencies, no build step, no JavaScript. A localhost-only `http.server`
app exists as a UI shell -- it is not infrastructure.

## Shape

```
                    ┌─ Library.save() ──→ ~/.bibi-tabs/*.txt
UltimateGuitar ─→ Song
  .search()         └─ HtmlRenderer ────→ browser
  .fetch()

bibi/song.py             Song, Line, SearchResult
bibi/chords.py           Chord, Transposer, spelling. Pure, no I/O.
bibi/fingering.py        Shape lookup, chords-db (MIT) in data/
bibi/diagram.py          Diagrams — SVG <symbol> per distinct chord
bibi/ultimate_guitar.py  UltimateGuitar — the only file that knows about UG
bibi/boite_a_chansons.py BoiteAChansons — likewise for boiteachansons.net
bibi/sources.py          Sources — routes a url, searches every site
bibi/library.py          Library — text files in a folder
bibi/render.py           HtmlRenderer — song page and landing page
bibi/server.py           Server — 127.0.0.1 only, stdlib http.server
bibi/config.py           Config — ~/.config/bibi-tabs.json, one setting
bibi/cli.py              App — wires them together
```

## Invariants — breaking one is a bug even if tests pass

1. **Transposition is display-only.** Never rewrite the stored file; a song
   always opens untransposed. Chords keep their original columns -- a shifted
   chord can widen (C -> C#) or narrow (Bb -> B), and the column is the only
   thing tying it to its syllable.
2. **Never reflow the sheet.** A chord means something only because of the
   column it occupies. Anything that trims, wraps, collapses whitespace or
   re-indents the body is a bug, however tidy the result looks.
3. **Site knowledge stays in its adapter.** Nothing outside `ultimate_guitar.py`
   and `boite_a_chansons.py` knows what a `[ch]` tag is or that either site
   exists; `sources.py` only routes. **No abstract base class** -- two classes
   with the same three methods is what duck typing is for.
4. **Songs are plain text**, readable without this program. The library outlives
   the tool. Default `~/.bibi-tabs/`, moveable. Never default it into the repo --
   copyrighted content does not belong in git.
5. **Zero dependencies.** Needing a package is a reason to question the feature.
6. **Small classes, one job each.**
7. **The server stays local.** Bind `127.0.0.1`. It fetches on the user's
   behalf, so the host is validated by parsing, never substring-matching --
   any page in the browser can aim a GET at localhost.
8. **State changes are POST.** Save and delete are forms, never links. A GET
   that deletes gets fired by prefetch and by back-navigation.
9. **Reading is not keeping.** `/view` renders without saving. Only the Save
   button writes to the library.

## Negative constraints — do not

- Do not add capo shifting, sync, accounts, a web framework, phone support, or
  a second site adapter. All deliberately cut. Transposition and diagrams
  arrived on request.
- Do not persist a transposition. Base 0 is the only state a song has.
- Do not expose the server beyond 127.0.0.1, and do not fetch a host the source
  does not own.
- Do not auto-save a song just because it was opened.
- Do not add a dependency without asking.
- Do not add configuration or plugin systems. Adding a third source means one
  more class in the `Sources` list, nothing else.
- Do not make anything load-bearing depend on the chord-line heuristic.
- Do not build sharing, republishing, or bulk downloading. Personal tool.

## Gotchas

- UG sheet path: `store.page.data.tab_view.wiki_tab.content`, inside an
  HTML-escaped JSON blob in `<div class="js-store">`. Verified 2026-08-02.
- `[ch]` markers overlay already-aligned text — stripping them keeps columns
  correct. Do not "fix" spacing afterwards.
- UG serves CRLF; normalise on parse.
- Pro tabs have no `wiki_tab.content` and raise `NotAChordPage`. Correct.
- Scraping UG breaks their ToS — a knowing choice for personal use.
- Search results include paid "Pro" entries with no sheet; filter on
  `type == "Chords"` and host `tabs.ultimate-guitar.com`.
- Slugs fold accents (`Drôle` → `drole`); dropping them gives `dr-le`.
- Boîte à Chansons anchors chords inline between syllables, so `lay_out` builds
  their columns. Roman-numeral capo, POST search, and a hidden
  `divPartitionPerso` copy on the page that must not be read.
- `Song.site` is blank on songs saved before there were two sites; they show no
  label until re-saved. Deliberate, not a migration.
- Enharmonic spelling comes from the target key on the circle of fifths, not a
  fixed table. Stops at twelve practical names: Gb major prints `B`, not `Cb`.
- Markup inside `<pre>` must add no characters, or columns break and copying
  the sheet pastes chords twice. The popup is absolutely positioned and empty
  of text for exactly this reason.
- `<pre>` must not have an overflow container -- it clips the diagram popups.
- Diagrams are one `<symbol>` per distinct chord plus `<use>` refs; inlining
  each occurrence would quadruple the page.
- One fret marker per diagram, left margin, `2fr` format. Barre row if there is
  a barre, else the top row when base_fret > 1, else nothing. It is the fret,
  never the finger.
- Some `fingers` rows use `-1` for "no finger". Test `> 0`, not truthiness.
