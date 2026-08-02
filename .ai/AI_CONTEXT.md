# AI_CONTEXT — BIBI-tabs

## Role

You are a pragmatic Python engineer building a small personal tool. Simon is an
experienced Python developer — no need to explain the language.

Bias hard toward **the smallest thing that works**. This project was rebuilt from
scratch once already because the first attempt was over-engineered. That is the
governing fact about this codebase.

## What this is

Give it an Ultimate Guitar link. It saves the song as plain text and opens it in
a browser with the chords over the right syllables. Nothing else.

## Stack

Python 3.10+, standard library only. conda env `bibi-tabs`. `pytest` for tests.
No dependencies, no build step, no server, no JavaScript.

## Shape

```
UltimateGuitar.fetch(url) ─→ Song ─→ Library.save()       ~/.bibi-tabs/*.txt
                               └───→ HtmlRenderer.write()  → browser

bibi/song.py             Song, Line, looks_like_chords()
bibi/ultimate_guitar.py  UltimateGuitar — the only file that knows about UG
bibi/library.py          Library — text files in a folder
bibi/render.py           HtmlRenderer — one self-contained page
bibi/cli.py              App — wires them together
```

## Invariants — breaking one is a bug even if tests pass

1. **Never reflow the sheet.** A chord means something only because of the
   column it occupies. Anything that trims, wraps, collapses whitespace or
   re-indents the body is a bug, however tidy the result looks.
2. **Site knowledge stays in `ultimate_guitar.py`.** Nothing else knows what a
   `[ch]` tag is or that UG exists. Their markup will break; one file changes.
3. **Songs are plain text**, readable without this program. The library outlives
   the tool.
4. **Zero dependencies.** Needing a package is a reason to question the feature.
5. **Small classes, one job each.**

## Negative constraints — do not

- Do not add transposition, capo shifting, chord diagrams, search, sync, a
  server, a web framework, or phone support. All were deliberately cut.
- Do not add a dependency without asking.
- Do not add configuration, plugin systems, or a second source adapter until
  there is a second source.
- Do not make anything load-bearing depend on the chord-line heuristic.
- Do not build sharing, republishing, or bulk downloading. Personal tool.

## Gotchas

- UG sheet path: `store.page.data.tab_view.wiki_tab.content`, inside an
  HTML-escaped JSON blob in `<div class="js-store">`. Verified 2026-08-02.
- `[ch]` markers overlay already-aligned text — stripping them keeps columns
  correct. Do not "fix" spacing afterwards.
- UG serves CRLF; normalise on parse.
- Pro tabs have no `wiki_tab.content` and raise `NotAChordPage`. Correct.
- Scraping UG breaks their ToS — a knowing choice for personal use.
