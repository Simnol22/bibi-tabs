# RELEVANT_STATE — BIBI-tabs

## Current State

**V1.9 works.** `bibi` opens a local page: search box, saved songs underneath.
Search UG, open a result to read it, press **Save** to keep it, `×` to remove
it. Opening a song no longer saves it.

Verified end to end against live UG, not just by unit test: view returned 200
with the library still empty, save wrote the file and redirected to the sheet,
re-viewing showed "Saved" with no button, delete emptied the library.

There is also a Settings page (the song folder is configurable, songs move with
it), a transposer on every song page, and chord diagrams on hover or tap.

187 tests, no network. conda env `bibi-tabs` (python 3.11), zero dependencies.

## In flight

Nothing.

## Editing chords (2026-08-02)

- **Text fields, not drag-and-drop.** Moving a chord needs sub-character
  precision and there is no JavaScript here; arrow buttons would mean a page
  reload per column. Each chord line becomes a monospace field in place, with
  its lyric static beneath -- spaces move, clearing deletes, typing adds. `ch`
  units make a field's columns line up exactly with the lyric.
- **Unlocking discards the transposition.** This is the trap the very first
  architecture warned about: an edit saved against a view shifted to D would
  write D chords into a song stored in C. Editing is always the stored key.
- **Lyrics have no field at all**, so nothing submitted can reach them. Scope
  was chords, and it makes accidental damage unrepresentable.
- **An empty "add" field only where there is no chord line already.** Emitting
  one everywhere put a blank row between every chord and its lyric, which broke
  the pairing the feature exists for. Caught by a test, not by eye.
- **`keep_blank_values=True` on the form parse.** Without it a cleared field
  vanishes from the POST, and "delete this chord line" would silently do nothing.

## The fret marker (2026-08-02)

Simon asked for "which number should it be barred at" and I read it as the
finger. He meant the fret. F#m barres the 2nd fret with the first finger, so the
diagram said "1" where he expected "2" -- and he was right, because a bare
number beside a barre reads as a position, not a finger.

Now: one marker, left margin, `2fr`. The suffix is the actual fix -- it removes
the ambiguity that caused the misread in the first place. It labels the barre's
row, or the top row when the grid starts up the neck, or nothing for an open
shape at the nut. Two numbers on opposite sides was what made either one
ambiguous, so there is only ever one.

The finger number for a barre is gone entirely. Accepted: it is 1 on the large
majority of shapes, and the fret is the thing you actually need.

## Bug worth remembering (2026-08-02)

**`bibi` searched only Ultimate Guitar for one commit**, while every test
passed. `cli.App.__init__` built its own `UltimateGuitar()` and handed it to the
server, so the server's `Sources()` default never applied. Every end-to-end
check had constructed `Server(...)` directly -- verifying through a path the
user never takes.

The lesson is in `TestCliWiring`: the command builds its own objects, so it can
silently disagree with the server's defaults. Verify through `bibi`, not through
a hand-built `Server`.

## Decisions from the second source (2026-08-02)

- **No abstract base class.** Two classes with `matches`/`fetch`/`search`, held
  in a list. An interface for two implementations is guesswork about the third.
- **Their format is the mirror image of UG's.** UG gives pre-aligned text with
  markers laid over it; Boîte à Chansons anchors chords inline between
  syllables, so the columns must be *built*. That made `lay_out` shared with the
  transposer instead of duplicated -- both place tokens at columns and push
  right by the minimum on collision.
- **Search results are interleaved, not concatenated.** UG returns 15 for a
  well-known song and BAC 4; appending would bury the smaller site entirely.
- **A failing site does not lose the other's results.** Each search is caught
  separately.
- **`Song.site` is stored, not derived from the URL.** Keeps the renderer from
  needing to know about sites. Songs saved before this show no label until
  re-saved -- accepted rather than migrated.
- **Site labels in all three places**, as Simon suggested: search rows (needed
  once results interleave), library rows (provenance when a sheet looks wrong),
  and the song page, where it just names the link that was already there.

## Decisions from barre labelling (2026-08-02)

- **A barre gets one number, in the left margin.** Repeating the finger number
  on every string it covers was noise -- Simon's call, and right.
- **The barre finger is read from the data, not assumed.** 2048 of 3283 shapes
  have a barre, and they use fingers 1, 2, 3 *and* 4, so a hardcoded "1" would
  be wrong on real chords (C6 barres with 3).
- **Left margin for the barre finger, right for the base fret**, so the two
  numbers can never be mistaken for each other. Padding went 14 -> 18 to fit.
- **The diagram box is now fixed.** The dataset never exceeds four frets, so
  height is constant -- which also fixed a latent mismatch where the outer
  `<svg viewBox>` said 104x120 while the symbol computed its own size.
- **`fingers` sometimes holds `-1` rather than `0`** for a muted string. Found
  in F's second voicing; truthiness would have printed "-1" on the diagram.

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
- Boîte à Chansons search has no ratings, so those rows show nothing there.
- BAC's "Artistes" search section is ignored; only song links are used.
- The transposer reloads the page, so it loses scroll position on a long song.
- Only the first (most common) voicing is shown; alternates are in the data.
- A barre is drawn across its full span even where a higher-fretted finger sits
  inside it, which is how printed charts do it, but it can look odd.
- A chord the dataset lacks simply gets no popup, silently.
