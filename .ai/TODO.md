# TODO — BIBI-tabs

## Current Sprint

V1.1 is done: search, fetch, read. Verified end to end against live UG. Nothing
in flight. Next step is Simon using it on real songs and reporting what's wrong.

- [ ] Use it for a week; note anything that reads badly
- [ ] Check a song with a `[tab]`-heavy intro (riff notation, not chords)
- [ ] Check a song whose chord line runs past the end of the lyric
- [ ] Decide whether search needs an artist filter (title-only today)
- [ ] Consider moving songs somewhere visible in Finder (`~/.bibi-tabs` is hidden)

---

## V1 — done

- [x] conda env `bibi-tabs`, python 3.11, zero dependencies
- [x] `Song` / `Line` + the ≥80% chord-line test
- [x] `UltimateGuitar` — js-store JSON, `[ch]`/`[tab]` stripping, CRLF, metadata
- [x] `Library` — plain text in `~/.bibi-tabs/`, save / load / find
- [x] `HtmlRenderer` — self-contained page, light and dark, printable
- [x] `App` / CLI — url, saved-song lookup, `--list`, `--no-open`
- [x] 26 tests, no network
- [x] Verified against a live UG page: columns intact, no leftover markers
- [x] Old SvelteKit + FastAPI stack removed (in git history at `8ed0bb1`)

## V1.1 — search UI, done

- [x] `UltimateGuitar.search()` — title search, Pro entries filtered, votes-first
- [x] `SearchResult` in `song.py`, so nothing outside the adapter knows about UG
- [x] `HtmlRenderer.index()` — search box, results with rating, saved songs
- [x] `Server` — stdlib `http.server`, `127.0.0.1` only, `/`, `/search`, `/add`, `/song/<slug>`
- [x] Host validated by parsing, not substring; path traversal rejected
- [x] `bibi` with no arguments opens the app; `--port` to move it
- [x] Slugs fold accents (`Drôle` → `drole`), found from real use

## V1.2 — save/delete, done

- [x] `/view?url=` renders a fetched song **without** saving it
- [x] Save button (POST `/save`) puts it in the library; already-saved says so
- [x] `←  Library` on every server-rendered song page, absent from the CLI's
      standalone file where it would be a dead link
- [x] `×` on each landing-page row (POST `/delete`, with a confirm)
- [x] Stateless preview: saving re-fetches rather than caching the song
- [x] Verified end to end -- view leaves the library empty, save writes, delete removes

## V1.3 — settings, done

- [x] `Config` — `~/.config/bibi-tabs.json` (honours `XDG_CONFIG_HOME`), one setting
- [x] Settings page, linked from the landing page
- [x] Changing the folder **moves the songs**, never overwriting a name already there
- [x] Relative paths refused; a corrupt config falls back instead of crashing
- [x] Default stays `~/.bibi-tabs/` so nothing moved under Simon
- [x] Verified end to end: song moved, config persisted, library re-listed

## V1.4 — transposition, done

- [x] `bibi/chords.py` — `Chord` parse/format, `Transposer`, `transpose_key`. Pure.
- [x] `− 0 +` control on saved song pages, with a reset when non-zero
- [x] Chords re-anchored at their original columns; collisions push right by one
- [x] Spelling from the target key's circle-of-fifths position, flats or sharps
- [x] Falls back to the accidentals already on the sheet when the key is unknown
- [x] Shift lives in the URL, never in the file — songs always open at 0
- [x] Header shows the transposed key with the original struck through
- [x] `?t=` clamped to ±11 and non-numeric input ignored
- [x] Verified on a real song: columns held at 0/5/9/13 across -1, +1, +2

- [ ] Transposition on the preview page too? Left out because each click would
      re-fetch the UG page. Only worth it if Simon actually wants it there.

## Possible, only if actually missed

Nothing here is planned. Listed so the reasoning isn't relitigated each time.

- [ ] Chord diagrams — chords-db (MIT) was already vetted, see `8ed0bb1`
- [ ] A second site adapter — `UltimateGuitar` already has `matches()`, so the
      shape is there; do not add an abstract base class for one implementation
- [ ] `bibi --edit <song>` to open the text file in `$EDITOR`
