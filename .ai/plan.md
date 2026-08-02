# plan.md — BIBI-tabs

## Goal

Paste an Ultimate Guitar link, get the song on screen with the chords over the
right syllables, keep it so it works without a connection. Nothing else.

## Principles

1. **Smallest thing that works.** A personal tool that stays readable for years
   beats a feature-complete one you can't follow. This was learned the hard way
   — see the history below.
2. **Own the data.** Plain text files in a folder. Readable and editable with no
   special program; the library survives this tool being abandoned.
3. **The alignment is the product.** Everything else is decoration.
4. **Isolate the fragile part.** Scraping breaks. One file knows about UG.

## History — why V1 looks like this

The first attempt was a SvelteKit PWA with a FastAPI backend, IndexedDB, a sync
engine, transposition, capo handling, key detection, chord diagrams, ChordPro
parsing and an edit mode. It reached a working library-and-player before Simon
called it: too complicated, too many features, and the one thing he actually
wanted — a UG link opening as a readable sheet — was the one thing missing.

Rebuilt as a Python CLI. Roughly 300 lines replaced roughly 4000. Kept in git
history at `8ed0bb1` if any of it is ever wanted back.

The deciding constraint: a browser **cannot** fetch a UG page (CORS), so the web
version needed a server running just to read a link. Python has no such problem.

## Modules

| Module | Responsibility |
|---|---|
| `bibi/song.py` | `Song`, `Line`, and the chord-line test. Pure. |
| `bibi/ultimate_guitar.py` | Fetch and parse a UG page. All site knowledge. |
| `bibi/library.py` | Save, load and find text files in `~/.bibi-tabs/`. |
| `bibi/render.py` | One self-contained HTML page. |
| `bibi/cli.py` | `App` — argument handling and wiring. |

## Done

V1 works: fetch, save, render, open, list.

## Explicit non-goals

- Transposition, capo shifting, chord diagrams.
- In-app search, a library browser beyond `--list`.
- Sync, accounts, a server, a phone app.
- Audio, tab (six-string) rendering, PDF export.
- A second site adapter, until there is a real need for one.
- Anything that shares or republishes fetched songs.
