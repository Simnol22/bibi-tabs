# RELEVANT_STATE — BIBI-tabs

## Current State

**V1.5 works.** `bibi` opens a local page: search box, saved songs underneath.
Search UG, open a result to read it, press **Save** to keep it, `×` to remove
it. Opening a song no longer saves it.

Verified end to end against live UG, not just by unit test: view returned 200
with the library still empty, save wrote the file and redirected to the sheet,
re-viewing showed "Saved" with no button, delete emptied the library.

There is also a Settings page (the song folder is configurable, songs move with
it), a transposer on every song page, and chord diagrams on hover or tap.

126 tests, no network. conda env `bibi-tabs` (python 3.11), zero dependencies.

## In flight

Nothing.

## Decisions from diagrams (2026-08-02)

- **chords-db restored from git rather than re-downloaded.** Its licence (MIT,
  © 2016 David Rubert) was already verified at `8ed0bb1`, and the flattened,
  midi-stripped 256 KB file was still in history.
- **One `<symbol>` per distinct chord, `<use>` per occurrence.** Wonderwall has
  154 chord popups over 5 shapes; inlining each would have made a 150 KB page
  instead of 35 KB.
- **The popup carries no caption.** A caption would be a second copy of the
  chord name inside the `<pre>`, so copying the sheet would paste every chord
  twice. Caught by the column test, not by eye.
- **`<pre>` lost its overflow container** because it clipped the popups. Long
  lines now scroll the page, which is what a monospace sheet wants anyway.
- **CSS `:hover` + `:focus`, no JavaScript.** `tabindex` makes it reachable by
  touch and keyboard, where hover does not exist.
- **Preview pages can transpose now**, backed by an 8-song in-memory cache.
  Without it every +/- click would re-fetch the whole UG page. This reverses
  the earlier "stateless preview" decision, and the cache is bounded so it
  cannot grow with browsing.

## Decisions from transposition (2026-08-02)

- **Chords existed only as a colouring regex before this.** `bibi/chords.py` is
  the first real chord model here — a port of the tested TypeScript at
  `5d438cf`, trimmed to what transposition needs.
- **Columns are re-anchored, not substituted.** A transposed chord can widen
  (`C` → `C#`) or narrow (`Bb` → `B`), and the column is the only thing tying a
  chord to its syllable. Each chord restarts at its original column; where a
  widened one would collide, the next moves right by exactly one rather than
  letting everything after it drift.
- **The shift lives in the URL (`?t=`), never in the file.** That is the whole
  of "only base 0 is saved" — there is no state to persist or reset.
- **± are plain links, not a form.** Transposing changes nothing on disk, so GET
  is correct and no JavaScript is needed.
- **Spelling follows the target key**, computed by shifting the song's stored
  `key`. Sharp keys get sharps, flat keys flats. With no usable key it falls
  back to whichever accidental the sheet already uses.
- **Twelve practical note names only.** Gb major prints `B`, not the
  theoretically correct `Cb`. Same call as the old TypeScript version; tested so
  it reads as a decision rather than an oversight.
- **Saved songs only.** On the preview page each ± would re-fetch the whole UG
  page. Left out until it is actually wanted.

## Decisions from settings (2026-08-02)

- **Songs stay out of the repo.** Simon asked about putting the folder at the
  repo root; declined because they are copyrighted lyrics, so a repo either
  commits them on push or has to ignore them -- and a repo-relative path breaks
  `bibi` run from any other directory. The real complaint was that
  `~/.bibi-tabs` is a dotfile and invisible in Finder, which the setting fixes.
- **Config lives outside the library**, at `~/.config/bibi-tabs.json`, for the
  obvious reason: it is the thing pointing at the library.
- **Changing the folder moves the songs**, via `shutil.move` rather than rename
  so it survives crossing a disk. A filename already at the destination is left
  alone rather than silently overwritten.
- **Default unchanged at `~/.bibi-tabs/`** so nothing moved under Simon's
  existing library. Migration is his choice, one click.
- **A corrupt or missing config falls back to defaults** rather than raising --
  losing a setting is annoying, refusing to start is worse.

## Decisions from save/delete (2026-08-02)

- **Preview is stateless.** `/view?url=` fetches and renders; pressing Save
  fetches again rather than holding the song in memory. One extra request buys
  no cache, no staleness, no memory that grows with browsing.
- **Save and delete are POST forms, not links.** A GET that writes or deletes
  gets fired by browser prefetch and by back-navigation. This is why the
  handler grew a `do_POST`.
- **Delete confirms via one inline `onsubmit="return confirm(...)"`.** The only
  JavaScript in the project. The alternative was a whole confirmation route.
- **The back link is conditional.** `render(song, home=...)` only draws it when
  given a home, because the CLI writes a `file://` page where `/` goes nowhere.
- **A song already in the library shows "Saved" instead of the button**, so the
  same URL can be opened twice without making a decision twice.

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
- The transposer reloads the page, so it loses scroll position on a long song.
- Only the first (most common) voicing is shown; alternates are in the data.
- A chord the dataset lacks simply gets no popup, silently.
