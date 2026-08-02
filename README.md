# BIBI-tabs

Search for a song, click it, read it with the chords sitting over the right
syllables. That's the whole program.

```bash
bibi          # opens the app: search box, and everything you've saved
```

Songs are kept as plain text in `~/.bibi-tabs/`, so once a song is fetched you
can read it with no connection — or with no BIBI-tabs, since they're just files.

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
                    ┌─ Library.save() ────→ ~/.bibi-tabs/*.txt
UltimateGuitar ─→ Song
   .search()        └─ HtmlRenderer ──────→ browser
   .fetch()
```

| | |
|---|---|
| `bibi/song.py` | `Song`, `Line`, `SearchResult`, and the chord-line test |
| `bibi/ultimate_guitar.py` | everything UG-specific, and nothing else is |
| `bibi/library.py` | plain text files in a folder |
| `bibi/render.py` | the song page and the landing page |
| `bibi/server.py` | localhost-only web app, stdlib `http.server` |
| `bibi/cli.py` | `App` — wires them together |

**Why there's a server at all.** A browser cannot fetch an Ultimate Guitar page
— CORS forbids it. So a search box in a web page needs something local to answer
the click. It binds to `127.0.0.1`, starts when you run `bibi`, and dies when
you close it. No deploy, no build step, no dependencies.

Because `/add?url=` fetches on your behalf, it checks the host properly before
making a request — substring matching would happily accept
`evil-ultimate-guitar.com`.

**The alignment is the point.** A UG page carries its sheet as JSON with chords
wrapped in `[ch]…[/ch]`, laid over text that is *already* column-aligned. Strip
the markers and the columns are still right — so the renderer just needs a
`<pre>` and the discipline not to reflow anything.

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

52 tests, no network — the UG page and search parsers are exercised against
synthetic pages, and the server's page building is tested without sockets.

## Not here on purpose

Transposition, capo shifting, chord diagrams, sync, phone support. V1 finds a
song and opens it. If one of those turns out to be missed, it can be added to a
program this small without much drama.
