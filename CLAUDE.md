# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project

**BIBI-tabs** — give it an Ultimate Guitar link, it saves the song and opens it
with the chords over the right syllables. That is the entire program.

Read `README.md` for how it fits together, `.ai/RELEVANT_STATE.md` for what is
currently in flight.

## Stack

Python 3.10+, **standard library only**. No dependencies, no build step. There
is a local `http.server` app, bound to `127.0.0.1` and started by the command --
that is a UI shell, not infrastructure.

**JavaScript only where nothing else can do the job.** Two places, both small
and both inline: a `confirm()` before deleting, and the auto-scroll script. The
diagrams, the transposer and the editor are all HTML and CSS, and must stay
that way -- reach for a script only after proving CSS cannot.

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
3. **Site-specific knowledge stays in its adapter.** `ultimate_guitar.py` and
   `boite_a_chansons.py`. Nothing else knows what a `[ch]` tag is or that either
   site exists; `sources.py` only routes URLs. When markup breaks, one file
   changes. There is deliberately **no abstract base class** -- two classes with
   the same three methods is what duck typing is for.
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
10. **Every line is editable, in the stored key.** Locking lyrics down sounded
    safer until a mistyped chord stopped reading as a chord line: the line then
    had no field, and the typo could not be undone from inside the app. A
    classifier must never decide whether something can be fixed. Unlocking
    still ignores the transposition, or an edit would re-key the song.
11. **Reading is not keeping.** `/view` renders without saving; only the Save
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
- **Nothing in the popup may be selectable text** -- the voicing arrows are
  drawn in CSS from an empty element and the "2/4" counter lives inside the SVG
  symbol, because either one written as a character would paste with the sheet.
- **The voicing carousel is radios plus `:checked ~ span:nth-of-type(n)`.** It
  depends on every radio preceding every pane in the markup. Because they are
  one radio group, the left and right keys navigate voicings for free -- and
  the radios must stay focusable (offscreen, not `display:none`), or clicking an
  arrow drops focus and `:focus-within` closes the popup under the pointer.
- **One radio group per chord occurrence**, handed out by `next_group()`. One
  group shared across a song would blank every other diagram in it the moment a
  voicing was picked anywhere.
- **Every occurrence carries its whole carousel**, so a 134-chord sheet is
  184 KB rather than 35 KB. It is inert -- the popup is `display:none` until
  hover -- but if it ever needs cutting, cap the voicings, do not share DOM.
- **`<pre>` must not have an overflow container** -- it would clip the popups.
  Long lines scroll the page instead.
- **One fret marker per diagram**, left margin, reading `2fr`. It labels the
  barre's row when there is a barre, otherwise the top row when the grid starts
  up the neck. It is the *fret*, not the finger: a bare number beside a barre
  gets read as a fret, which is why it now carries "fr".
- **Some `fingers` rows use `-1` for "no finger"** where others use `0`. Test
  `> 0`, or a diagram prints "-1".
- **`<form>` must impose no layout.** The edit screen wraps the whole page in
  one, so a global `form { display:flex }` lays nav, header and sheet out in a
  row. Only `.bar` is flex.
- **The auto-scroll control is `position:fixed`** for a reason: it is the one
  control you reach for while the page is already moving, and a header-bound
  Stop button is a thousand pixels away by then.
- **Track the scroll position as a float and write it with `scrollTo`.**
  `scrollBy` rounds to whole pixels, and at 5 px/s the rounding is the entire
  movement -- the page would not move at all on the slowest setting.
- **Auto-scroll must follow a reader who takes over**, not fight them. Each
  frame compares `scrollY` to where it thinks it is and re-anchors when they
  differ by more than 2px (rounding). Otherwise grabbing the scrollbar snaps
  you back on the next frame.
- **A chord can be wrapped in brackets** -- `(Dmaj7)` means an optional chord,
  and is distinct from brackets *inside* a symbol like `C(add9)`. Bar lines and
  beat slashes count neither way in the chord-line test. Both were found in a
  real song, where `G  (Dmaj7)` scored 1/2 and the line stopped being chords.
- **An unmistakable chord counts anywhere**, not only on a chord line -- real
  sheets put them in intro notes that never reach the threshold. `Dmaj7` is a
  chord wherever it sits; a lone `A`, or `Am`, is a word far more often, so
  those stay line-gated. Measured on four songs: 4 real chords gained, 4 false
  positives avoided, and every false positive was a single letter.
- **The chord-line test is a heuristic** (≥80% of tokens parse as chords). It
  only picks colour. Do not let anything load-bearing depend on it.
- **Pro tabs and tab-type pages have no `wiki_tab.content`** and raise
  `NotAChordPage`. That is correct behaviour, not a parsing failure.
- **`matches()` must parse the URL, never substring-match.** `evil-ultimate-guitar.com`
  contains `ultimate-guitar.com`.
- **Boîte à Chansons anchors chords inline**, between syllables, rather than in
  columns -- so their alignment is *built* by `lay_out`, not preserved. Their
  capo is a Roman numeral, their search is a POST, and their page carries a
  hidden `divPartitionPerso` copy that must not be read.
- **Scraping these sites is against their ToS.** A knowing choice for personal use. Do
  not build anything that shares, republishes or bulk-downloads.

## Context files

`.ai/` holds `AI_CONTEXT.md`, `plan.md`, `TODO.md`, `RELEVANT_STATE.md`. Keep
them current as a routine part of every session — no need to ask first. Reset
`RELEVANT_STATE.md` to a stub after every `git push`; the commit history is the
permanent record.
