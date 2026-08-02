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
| `bibi/library.py` | plain text files in a folder |
| `bibi/render.py` | the song page and the landing page |
| `bibi/server.py` | localhost-only web app, stdlib `http.server` |
| `bibi/config.py` | one small JSON file, one setting so far |
| `bibi/chords.py` | chord symbols, transposition, enharmonic spelling. Pure. |
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

**Chord lines are found by counting.** A line is chords when at least 80% of its
tokens parse as chord symbols. It only decides colour, so a wrong answer is a
mis-coloured line, never mangled text.

**Ultimate Guitar will break this.** Their markup changes. When it does,
`ultimate_guitar.py` is the only file to fix — that's why it's the only one that
knows what a `[ch]` tag is. Scraping their pages is also against their terms of
service; this is a personal tool and that was a deliberate call.

## Tests

```bash
pytest
```

100 tests, no network — the UG page and search parsers are exercised against
synthetic pages, and the server's page building is tested without sockets.

## Where songs live

Default is `~/.bibi-tabs/`. Change it in **Settings** — existing songs move with
it, and a name already at the destination is never overwritten.

Keep them **out of a git repository.** They're copyrighted lyrics, so a repo
either publishes them on push or has to ignore them, which defeats the point of
putting them there. The setting is stored separately, in
`~/.config/bibi-tabs.json`, since it's the thing pointing at the song folder.

## Not here on purpose

Capo shifting, chord diagrams, sync, phone support. Transposition arrived when
it was actually wanted. If one of those turns out to be missed, it can be added to a
program this small without much drama.
