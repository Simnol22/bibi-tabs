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
4. **Transposition is display-only.** The stored file is never rewritten, so a
   song always opens untransposed. Chords keep their original columns: a
   transposed chord can be wider or narrower, and the column is what ties it to
   its syllable.
5. **Never reflow the sheet.** A chord is meaningful only because of the column
   it sits in. Anything that trims, wraps, collapses whitespace or re-indents
   the body is a bug, however tidy it looks.
6. **Songs are plain text**, readable and editable without this program. The
   library must outlive the tool. Default `~/.bibi-tabs/`, moveable in Settings.
   Never default them inside the repo -- they are copyrighted, and a repo either
   commits them or ignores them.
7. **OOP, small classes.** One class, one job: `Song`, `Chord`, `Transposer`,
   `Shape`, `Diagrams`, `UltimateGuitar`, `Library`, `HtmlRenderer`, `Config`,
   `Server`, `App`.
8. **The server stays local and unprivileged.** Bind `127.0.0.1` only. It
   fetches on the user's behalf, so validate the host properly before every
   request -- any page in the browser can aim a GET at localhost.
9. **Anything that changes state is a POST.** Saving and deleting are forms,
   never links. A GET that deletes a file gets fired by browser prefetch and by
   back-navigation.
10. **Reading is not keeping.** `/view` renders without saving; only the Save
   button writes to the library.

## Known gotchas

- **UG's markup will break.** The sheet lives at
  `store.page.data.tab_view.wiki_tab.content` inside an HTML-escaped JSON blob
  in `<div class="js-store">`. Verified against a live page on 2026-08-02;
  treat it as unstable and re-check before debugging anything else.
- **`[ch]` markers sit on top of already-aligned text**, so stripping them
  leaves columns correct. Do not try to "fix" spacing afterwards.
- **UG serves CRLF.** Normalise on parse or every line gains a stray `\r`.
- **Enharmonic spelling comes from the target key's place on the circle of
  fifths**, never a fixed sharp/flat table -- otherwise transposed sheets read
  `Gb` where `F#` belongs. It stops at the twelve practical names: Gb major
  prints `B`, not the theoretically correct `Cb`. Deliberate, and tested.
- **Markup inside `<pre>` must add no characters.** Chords are wrapped in spans
  for the diagram popups; the popup is absolutely positioned and carries no
  text, or it would both break the columns and paste twice when copied.
- **`<pre>` must not have an overflow container** -- it would clip the popups.
  Long lines scroll the page instead.
- **A barre gets one number in the left margin**, not the same digit on every
  string it covers. It is not always finger 1 -- the dataset uses 2, 3 and 4 --
  so it cannot be hardcoded. Base fret lives in the right margin.
- **Some `fingers` rows use `-1` for "no finger"** where others use `0`. Test
  `> 0`, or a diagram prints "-1".
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
