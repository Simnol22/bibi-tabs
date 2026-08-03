# BIBI-tabs

Search for a song, read it with the chords sitting over the right syllables,
keep the ones you want. That's the whole program.

```bash
bibi          # opens the app: search box, and everything you've saved
```

Songs are kept as plain text in `~/.bibi-tabs/`, so once a song is fetched you
can read it with no connection — or with no BIBI-tabs, since they're just files.
**Settings** moves that folder anywhere you like, songs included.

## Install

No dependencies. Standard library only.

```bash
conda activate bibi-tabs      # python 3.10+
pip install -e .
```

## Use

```bash
bibi                          # the app — search, and your saved songs
bibi <ultimate-guitar-url>    # skip the search, fetch this one
bibi wonderwall               # open something already saved, no app needed
bibi --list                   # what's saved, in the terminal
bibi --port 9000              # if 8777 is taken
```

Without the install step, `python -m bibi …` works the same.

## How it works

```
search ─→ view ─→ [Save] ─→ ~/.bibi-tabs/*.txt ─→ landing page ─→ [×] gone
            │
            └─ reading a song does not keep it
```

Opening a search result only shows it. It joins your library when you press
**Save**, and leaves when you press **×** on the landing page. Every song page
has a link back to the library.

| | |
|---|---|
| `bibi/song.py` | `Song`, `Line`, `SearchResult`, and the chord-line test |
| `bibi/ultimate_guitar.py` | everything UG-specific, and nothing else is |
| `bibi/boite_a_chansons.py` | likewise for boiteachansons.net |
| `bibi/sources.py` | which site owns a URL; searches all of them |
| `bibi/library.py` | plain text files in a folder |
| `bibi/render.py` | the song page and the landing page |
| `bibi/server.py` | localhost-only web app, stdlib `http.server` |
| `bibi/config.py` | one small JSON file, one setting so far |
| `bibi/chords.py` | chord symbols, transposition, enharmonic spelling. Pure. |
| `bibi/fingering.py` | chord symbol to fret positions (chords-db, MIT) |
| `bibi/diagram.py` | a fret shape as an SVG `<symbol>` |
| `bibi/cli.py` | `App` — wires them together |

**Why there's a server at all.** A browser cannot fetch an Ultimate Guitar page
— CORS forbids it. So a search box in a web page needs something local to answer
the click. It binds to `127.0.0.1`, starts when you run `bibi`, and dies when
you close it. No deploy, no build step, no dependencies.

Because the server fetches on your behalf, it checks the host by parsing the URL
before making any request — substring matching would happily accept
`evil-ultimate-guitar.com`. Saving and deleting are `POST`, never links: a `GET`
that deletes a file gets fired by browser prefetch and by going back in history.

**The alignment is the point.** A UG page carries its sheet as JSON with chords
wrapped in `[ch]…[/ch]`, laid over text that is *already* column-aligned. Strip
the markers and the columns are still right — so the renderer just needs a
`<pre>` and the discipline not to reflow anything.

**Transposing never touches the file.** The song page has a `− 0 +` control; the
shift lives in the URL, so a song always opens in the key it was written in.
Chords are re-anchored at their original columns, because transposing can widen
a chord (`C` to `C#`) or narrow one (`Bb` to `B`) and the column is the only
thing tying a chord to its syllable.

Spelling follows the key the song lands *in*, not a fixed table — up one from A
is `Bb`, never `A#`. It stops at the twelve practical note names, so Gb major
prints `B` where strict theory wants `Cb`.

**Hover or tap a chord to see its shape — and every other way to play it.** Most
chords come with four voicings; arrows step through them and a small counter
says which one you are on. It is a radio group under the surface, so the left
and right keys work too. Diagrams come from
[chords-db](https://github.com/tombatossals/chords-db) (MIT, © 2016 David
Rubert), bundled at 256 KB so they work offline. A barre is one finger doing one
thing, so it gets one number in the left margin rather than the same digit
repeated across every string it covers; the base fret stays in the right margin
so the two can't be confused. Each distinct chord is drawn
once as an SVG `<symbol>` and referenced with `<use>` — a sheet with 154 chord
popups over 5 shapes stays a 35 KB page. Shown with CSS `:hover` and `:focus`,
so it needs no JavaScript and still works on touch and by keyboard.

**Auto-scroll while you play.** A fixed control in the corner starts the sheet
moving and takes a speed from 1 to 10 — around 5 to 50 pixels a second, changed
without stopping. It follows you if you grab the scrollbar mid-song, and stops
at the bottom. This is the one thing in the program that needs JavaScript;
nothing else can move the viewport.

**Click the lock to edit.** Each line becomes a monospace field sitting exactly
where it was: spaces move a chord, clearing the field deletes the line, and
every lyric without chords gets an empty field above it so you can add one.
Lock again to save. Every line is editable, including lyrics — a mistyped chord
stops the line reading as chords, and if only chord lines had fields the typo
could never be undone from inside the app.

Unlocking always shows the **stored** key, whatever you were transposed to.
Saving an edit made against a shifted view would silently re-key the song.

**Chord lines are found by counting.** A line is chords when at least 80% of its
tokens parse as chord symbols. It only decides colour, so a wrong answer is a
mis-coloured line, never mangled text.

**Two sites, two shapes.** Ultimate Guitar ships a JSON blob of already-aligned
text with `[ch]` markers laid over it. Boîte à Chansons ships HTML with chords
anchored *inline* between syllables, so their columns have to be built rather
than preserved. Both end up as the same plain chord-over-lyric text.

Search asks both and interleaves the answers, so UG's dozens of versions don't
bury Boîte à Chansons's handful. Every result, library row and song page says
which site it came from.

**Their markup will break this.** When it does, one adapter file is the only
thing to fix — which is why nothing outside them knows what a `[ch]` tag is.
Scraping is also against these sites' terms of service; this is a personal tool
and that was a deliberate call.

## Tests

```bash
pytest
```

160 tests, no network — the UG page and search parsers are exercised against
synthetic pages, and the server's page building is tested without sockets.

## Where songs live

Default is `~/.bibi-tabs/`. Change it in **Settings** — existing songs move with
it, and a name already at the destination is never overwritten.

Keep them **out of a git repository.** They're copyrighted lyrics, so a repo
either publishes them on push or has to ignore them, which defeats the point of
putting them there. The setting is stored separately, in
`~/.config/bibi-tabs.json`, since it's the thing pointing at the song folder.

## Not here on purpose

Capo shifting, sync, phone support. Transposition, diagrams and a second site
arrived when they were actually wanted. If one of those turns out to be missed, it can be added to a
program this small without much drama.
