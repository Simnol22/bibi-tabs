# RELEVANT_STATE — BIBI-tabs

## Current State

**V1.1 works.** `bibi` opens a local page with a search box and your saved
songs. Search hits Ultimate Guitar, results show version and rating, clicking
one fetches and saves it and drops you on the sheet.

Verified end to end against live UG, not just by unit test: search returned 15
filtered results, following the top one gave a 303 to the song page with 44
chord lines and no leftover markers.

52 tests, no network. conda env `bibi-tabs` (python 3.11), zero dependencies.

## In flight

Nothing.

## Decisions from the search UI (2026-08-02)

- **A local server was unavoidable.** A browser cannot fetch a UG page (CORS),
  so a search box in a page needs something local to answer the click. Stdlib
  `http.server`, `127.0.0.1` only, starts and dies with the command.
- **`/add?url=` validates the host by parsing.** It is a GET on localhost, so
  any page in the browser can aim at it. `matches()` was substring-based and
  would have accepted `evil-ultimate-guitar.com`; it now parses and compares
  the hostname. Path traversal on `/song/<slug>` is rejected too.
- **Paid "Pro" search results are filtered out** — they carry no sheet and would
  only ever error. Keep `type == "Chords"` on host `tabs.ultimate-guitar.com`.
  For "wonderwall" that trims 52 raw hits to 15 usable ones.
- **Results sort by vote count**, so the version everyone actually plays is on
  top. Rating alone would float a 4.9 with 12 votes above a 4.8 with 11,000.
- **Slugs fold accents.** Found from real use: `Drôle de temps` was saving as
  `dr-le-de-temps`. NFKD-folded now, so `drole-de-temps`.
- **Page building is separate from serving.** `Server.index_page()` and friends
  return strings and touch no sockets, so they are tested without binding a port.

## The rewrite (2026-08-02)

The SvelteKit PWA + FastAPI backend was deleted and replaced with Python.
Simon's call: too complicated, too many features, and the one thing he wanted —
a UG link opening as a readable sheet — was the one thing it couldn't do.
Preserved in git history:

| | |
|---|---|
| `f0646e4` | Phase 0 scaffold |
| `5d438cf` | music theory + ChordPro, 84 tests — port from here if transposition is ever wanted |
| `8ed0bb1` | library, player, chord diagrams; includes the vetted MIT chords-db dataset |

## UG page structure, verified 2026-08-02

Re-check this before debugging anything UG-related; it is the part that rots.

- Sheet: `store.page.data.tab_view.wiki_tab.content`, in an HTML-escaped JSON
  blob in `<div class="js-store" data-content="…">`.
- Metadata: `data.tab.song_name` / `.artist_name` / `.tonality_name`, and
  `data.tab_view.meta.capo`.
- Search: `ultimate-guitar.com/search.php?search_type=title&value=<q>`, same
  js-store shape, results under `data.results` with `song_name`, `artist_name`,
  `type`, `version`, `rating`, `votes`, `tab_url`.
- Chords are `[ch]…[/ch]`; aligned sections wrapped in `[tab]…[/tab]`.
- **Markers overlay already-aligned text.** Confirmed on a real page: chords at
  columns 0, 5, 9, 13 above a 19-character lyric, unchanged after stripping.
- Line endings are CRLF.

## Known limits

- `[tab]` blocks holding riff notation rather than chords render as-is.
  Untested against a tab-heavy song.
- A chord line running past the end of its lyric is untested.
- Search is by title only; there is no artist filter.
- Only Ultimate Guitar.
