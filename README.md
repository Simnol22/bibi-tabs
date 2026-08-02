# BIBI-tabs

Give it an Ultimate Guitar link. It saves the song and opens it with the chords
sitting over the right syllables. That's the whole program.

```bash
bibi https://tabs.ultimate-guitar.com/tab/oasis/wonderwall-chords-27596
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
bibi <ultimate-guitar-url>    # fetch it, keep it, open it
bibi wonderwall               # open something already saved
bibi --list                   # what's saved
bibi <url> --no-open          # save without launching a browser
```

Without the install step, `python -m bibi …` works the same.

## How it works

```
UltimateGuitar.fetch(url) ─→ Song ─→ Library.save()      ~/.bibi-tabs/*.txt
                               └───→ HtmlRenderer.write() → open in browser
```

| | |
|---|---|
| `bibi/song.py` | `Song`, `Line`, and the chord-line test |
| `bibi/ultimate_guitar.py` | everything UG-specific, and nothing else is |
| `bibi/library.py` | plain text files in a folder |
| `bibi/render.py` | one self-contained HTML page |
| `bibi/cli.py` | `App` — wires the four together |

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

26 tests, no network — the UG parser is exercised against a synthetic page.

## Not here on purpose

Transposition, capo shifting, chord diagrams, search, sync, phone support. V1
opens a song. If one of those turns out to be missed, it can be added to a
program this small without much drama.
