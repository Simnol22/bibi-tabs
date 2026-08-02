# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project

**BIBI-tabs** — give it an Ultimate Guitar link, it saves the song and opens it
with the chords over the right syllables. That is the entire program.

Read `README.md` for how it fits together, `.ai/RELEVANT_STATE.md` for what is
currently in flight.

## Stack

Python 3.10+, **standard library only**. No dependencies, no build step, no
JavaScript. There is a local `http.server` app, bound to `127.0.0.1` and started
by the command -- that is a UI shell, not infrastructure.

```bash
conda activate bibi-tabs
pip install -e .
pytest
bibi <ultimate-guitar-url>
```

## The rules that keep this small

1. **Minimalism above all.** This project was already rebuilt once for being
   over-engineered. No feature that has not been asked for. No abstraction with
   one implementation. No "we'll need it later" — later can add it.
2. **Zero dependencies.** If something needs a package, that is a reason to
   question the something. The standard library has covered every need so far.
3. **Site-specific knowledge stays in `ultimate_guitar.py`.** Nothing else in
   the codebase knows what a `[ch]` tag is, or that Ultimate Guitar exists. When
   their markup breaks, exactly one file changes.
4. **Never reflow the sheet.** A chord is meaningful only because of the column
   it sits in. Anything that trims, wraps, collapses whitespace or re-indents
   the body is a bug, however tidy it looks.
5. **Songs are plain text.** `~/.bibi-tabs/*.txt`, readable and editable without
   this program. The library must outlive the tool.
6. **OOP, small classes.** One class, one job: `Song`, `UltimateGuitar`,
   `Library`, `HtmlRenderer`, `Server`, `App`.
7. **The server stays local and unprivileged.** Bind `127.0.0.1` only. `/add`
   fetches on the user's behalf, so validate the host properly before every
   request -- any page in the browser can aim a GET at localhost.

## Known gotchas

- **UG's markup will break.** The sheet lives at
  `store.page.data.tab_view.wiki_tab.content` inside an HTML-escaped JSON blob
  in `<div class="js-store">`. Verified against a live page on 2026-08-02;
  treat it as unstable and re-check before debugging anything else.
- **`[ch]` markers sit on top of already-aligned text**, so stripping them
  leaves columns correct. Do not try to "fix" spacing afterwards.
- **UG serves CRLF.** Normalise on parse or every line gains a stray `\r`.
- **The chord-line test is a heuristic** (≥80% of tokens parse as chords). It
  only picks colour. Do not let anything load-bearing depend on it.
- **Pro tabs and tab-type pages have no `wiki_tab.content`** and raise
  `NotAChordPage`. That is correct behaviour, not a parsing failure.
- **`matches()` must parse the URL, never substring-match.** `evil-ultimate-guitar.com`
  contains `ultimate-guitar.com`.
- **Scraping UG is against their ToS.** A knowing choice for personal use. Do
  not build anything that shares, republishes or bulk-downloads.

## Context files

`.ai/` holds `AI_CONTEXT.md`, `plan.md`, `TODO.md`, `RELEVANT_STATE.md`. Keep
them current as a routine part of every session — no need to ask first. Reset
`RELEVANT_STATE.md` to a stub after every `git push`; the commit history is the
permanent record.
