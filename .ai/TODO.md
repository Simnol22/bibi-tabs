# TODO — BIBI-tabs

## Current Sprint

V1.1 is done: search, fetch, read. Verified end to end against live UG. Nothing
in flight. Next step is Simon using it on real songs and reporting what's wrong.

- [ ] Use it for a week; note anything that reads badly
- [ ] Check a song with a `[tab]`-heavy intro (riff notation, not chords)
- [ ] Check a song whose chord line runs past the end of the lyric
- [ ] Decide whether search needs an artist filter (title-only today)

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

## Possible, only if actually missed

Nothing here is planned. Listed so the reasoning isn't relitigated each time.

- [ ] Transposition — would need chord parsing back; there is a tested
      TypeScript implementation at `5d438cf` to port if it comes to it
- [ ] Chord diagrams — chords-db (MIT) was already vetted, see `8ed0bb1`
- [ ] A second site adapter — `UltimateGuitar` already has `matches()`, so the
      shape is there; do not add an abstract base class for one implementation
- [ ] `bibi --edit <song>` to open the text file in `$EDITOR`
