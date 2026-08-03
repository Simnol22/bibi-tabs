# TODO — BIBI-tabs

## Current Sprint

V1.12 is committed. **V1.13 — auto-scroll and multiple voicings — is written and
tested but uncommitted, and Simon has not seen either in a browser.**

- [ ] Simon: check auto-scroll on a real song — is level 2 (10 px/s) a sensible
      default, and does the pill sit somewhere that isn't in the way?
- [ ] Simon: check the voicing arrows — do they stay open while you click them?
- [ ] Decide whether 184 KB per sheet is too heavy (cap voicings at 3 if so)
- [ ] Use it for a week; note anything that reads badly
- [ ] Check a song with a `[tab]`-heavy intro (riff notation, not chords)
- [ ] Check a song whose chord line runs past the end of the lyric
- [ ] Decide whether search needs an artist filter (title-only today)
- [ ] Consider moving songs somewhere visible in Finder (`~/.bibi-tabs` is hidden)

Settled 2026-08-02: **this stays a personal tool.** Simon asked whether it could
go on the Play Store; the lyrics are licensed content that UG pays for and this
app would not, so no. Do not build sharing or distribution.

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

## V1.5 — diagrams, and transposing previews, done

- [x] Transposer now on preview pages too; the last 8 fetches are cached so
      clicking +/- does not re-hit Ultimate Guitar
- [x] `bibi/fingering.py` + `data/guitar.json` — chords-db (MIT), 256 KB,
      restored from `8ed0bb1` where its licence was already verified
- [x] `bibi/diagram.py` — SVG `<symbol>` per distinct chord, `<use>` per occurrence
- [x] Hover, tap or tab a chord to see its shape. CSS `:hover` + `:focus`, no JS
- [x] Popup carries no text, so columns hold and copying does not duplicate chords
- [x] `<pre>` overflow removed — it clipped the popups
- [x] Diagrams follow the transposition
- [x] Verified on a real song: 154 popups over 5 shapes, 35 KB page, columns intact

## V1.6 — barre labelling, done

- [x] Barred strings no longer each carry the same finger number
- [x] The barre finger goes once in the left margin; base fret stays right
- [x] Barre finger read from the data, since it is not always 1 (2, 3, 4 occur)
- [x] Fixed diagram box (dataset never exceeds 4 frets), so the outer `<svg>`
      viewBox finally matches the symbol's
- [x] `fingers` values of `-1` no longer print as a number

## V1.7 — Boîte à Chansons, done

- [x] `bibi/boite_a_chansons.py` — HTMLParser over `div#divPartition`
- [x] Inline chord anchors turned into columns via the shared `lay_out`
- [x] Roman-numeral capo, `tonalite` key, og:title for song and artist
- [x] POST search; menu links filtered out by path-segment count
- [x] `bibi/sources.py` — routes a url, searches both, interleaves the results
- [x] One site failing does not lose the other's results
- [x] `Song.site` + `SearchResult.source`; labels in search, library, song page
- [x] `lay_out` extracted so the transposer and the adapter share one rule
- [x] Verified end to end: fetched, saved with capo 1 from "Capo I", search
      returned 15 UG + 4 BAC interleaved
- [x] **Fix:** `cli.App` was still hardcoding `UltimateGuitar()`, so the actual
      `bibi` command searched one site while the tests passed. `TestCliWiring`
      now pins the command's own wiring.

## V1.8 — the fret marker, done

- [x] The number beside a barre is the **fret**, not the finger. F#m reads 2fr.
- [x] It carries "fr", so it cannot be read as a finger number again
- [x] One marker per diagram instead of two on opposite sides: barre row, else
      the top row when the grid starts up the neck, else nothing
- [x] Marker counts from base_fret, so grid-from-5 with a barre on row 2 is 6fr

## V1.9 — lock and edit, done

- [x] Lock icon on a saved song; `?edit=1` unlocks, "Lock and save" writes
- [x] Chord lines become monospace fields in place, `ch`-width so the grid
      lines up with the lyric beneath
- [x] Move with spaces, clear the field to delete, type into an empty one to add
- [x] Empty field only where there is no chord line already, or every lyric
      would be pushed a row from its chords
- [x] `Song.edited()` rebuilds the body; lyrics have no field and are untouched
- [x] Unlocking discards the transposition -- editing is always the stored key
- [x] `keep_blank_values=True`, or a cleared field would vanish instead of
      meaning "delete"
- [x] Verified over HTTP: moved a chord 4 columns, deleted a line, reloaded,
      re-read from disk

## V1.10 — editing polish, done

- [x] Fix the page shifting sideways while editing: `form { display:flex }` was
      global, and the edit screen wraps the whole page in a form
- [x] Non-chord tokens on a chord line render muted, so typos show once locked

## V1.11 — bracketed chords, and no more frozen lines, done

- [x] `(Dmaj7)` and `[Am]` parse as chords; `C(add9)` keeps its inner brackets
- [x] Bar lines and beat slashes count neither way in the chord-line test
- [x] Transposing preserves the brackets: `(Dmaj7)` +2 is `(Emaj7)`
- [x] **Every line is editable.** A mistyped chord used to make its line
      unclassifiable, which removed its field and froze the typo in place
- [x] Verified on the reported song: the line reads as chords, all lines editable

## V1.12 — chords among words, done

- [x] A chord standing in a line of words is coloured and hoverable, and shifts
      with the transposition like any other
- [x] Gated by `unambiguous_chord()`: a lone `A` or `Am` is a word far more
      often, so those still need a recognised chord line
- [x] Measured first on four real songs: 4 genuine chords gained, 4 false
      positives avoided, all four of them single letters
- [x] `_tokens()` now serves both paths instead of two near-copies

## V1.13 — auto-scroll and multiple voicings, written, not yet verified by hand

- [x] Fixed play/pause pill with a speed level 1–10, changeable mid-scroll
- [x] Speed kept in `localStorage`, so it carries between songs
- [x] Position tracked as a float and written with `scrollTo` — `scrollBy`
      rounds, and at 5 px/s the rounding is the whole movement
- [x] Re-anchors when the reader takes over, instead of snapping them back
- [x] Stops at the bottom; hidden when printing
- [x] **First JavaScript in the project.** Nothing else can move the viewport;
      the rule is now "only where nothing else can do the job"
- [x] Every voicing the dataset knows, arrows to step through, wrap-around
- [x] Radios + `:checked ~ span:nth-of-type(n)` — the carousel needs no script,
      and the radio group gives left/right key navigation free
- [x] Arrows drawn in CSS from an empty element, counter drawn inside the SVG
      symbol: nothing in the popup is selectable, so copying the sheet is clean
- [x] One radio group per occurrence, or picking a voicing blanks the rest
- [x] Verified the script against a stubbed DOM in node; sheet still strips
      back to exactly the stored text
- [ ] Not verified in a browser by Simon

## Possible, only if actually missed

Nothing here is planned. Listed so the reasoning isn't relitigated each time.

- [ ] A third site — one more class in the `Sources` list. Still no base class.
- [ ] `bibi --edit <song>` to open the text file in `$EDITOR`
