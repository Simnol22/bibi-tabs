# TODO — BIBI-tabs

## Current Sprint

V1 is done and works end to end against a live Ultimate Guitar page. Nothing is
in flight. Next step is Simon using it on real songs and reporting what's wrong.

- [ ] Use it for a week; note anything that reads badly
- [ ] Check a song with a `[tab]`-heavy intro (riff notation, not chords)
- [ ] Check a song whose chord line runs past the end of the lyric

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

## Possible, only if actually missed

Nothing here is planned. Listed so the reasoning isn't relitigated each time.

- [ ] Transposition — would need chord parsing back; there is a tested
      TypeScript implementation at `5d438cf` to port if it comes to it
- [ ] Chord diagrams — chords-db (MIT) was already vetted, see `8ed0bb1`
- [ ] A second site adapter — `UltimateGuitar` already has `matches()`, so the
      shape is there; do not add an abstract base class for one implementation
- [ ] `bibi --edit <song>` to open the text file in `$EDITOR`
