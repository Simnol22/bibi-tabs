# RELEVANT_STATE — BIBI-tabs

## Current State

**V1.12 is committed** (`2d42b9c`). `bibi` opens a local page: search box, saved
songs underneath. Search Ultimate Guitar and Boîte à Chansons, open a result to
read it, **Save** to keep it, `×` to remove it. Opening a song does not save it.

Also working: Settings (the song folder is configurable, songs move with it), a
transposer on every song page, chord diagrams on hover or tap, and a lock icon
that unlocks every line for editing in the stored key.

conda env `bibi-tabs` (python 3.11), zero dependencies, 226 tests, no network in
the suite.

## In flight — V1.13, not yet committed

Two features, both working and tested, neither verified by Simon in a browser.

**Auto-scroll.** A fixed pill in the bottom-right corner: play/pause and a speed
level from 1 to 10 (5 to 50 px/s). Speed changes without stopping and is kept in
`localStorage`, so it carries between songs.

**Multiple voicings.** Every chord popup now offers each shape the dataset knows
— four for most chords — with arrows to step through them and a "2/4" counter.

### Decisions behind them

- **This is the project's first real JavaScript**, ~25 lines inline for
  auto-scroll. Nothing else can move the viewport: CSS can animate content
  upward, but the sheet would then slide out from under its own chord popups,
  and the speed could not answer while it played. The rule in CLAUDE.md changed
  from "no JavaScript" to "JavaScript only where nothing else can do the job".
- **The voicing carousel needed none of it.** A radio per shape, a `<label>` per
  arrow, and `:checked ~ span:nth-of-type(n)` to swap panes. Because the radios
  are a group, the left and right keys step through voicings for free.
- **Nothing in the popup may be selectable text.** It sits inside the `<pre>`,
  so a character would paste when the sheet is copied — the same trap that
  removed the popup's caption back in V1.5. The arrows are therefore drawn in
  CSS from an empty element, and the "2/4" counter lives inside the SVG symbol,
  where selection cannot reach it. Verified: the sheet still strips back to
  exactly the stored text.
- **`Diagrams.next_group()` hands out one radio-group name per occurrence.** One
  shared group across a song would blank every other diagram the moment you
  picked a voicing anywhere.
- **The data was always there.** `shapes()` already returned every voicing,
  commonest first; `Diagrams.add` had been discarding all but `found[0]`.

### The cost, stated plainly

A real 134-chord sheet went from **35 KB to 184 KB**, because every occurrence
carries its own four-pane carousel. Nothing renders until hover (the popup is
`display:none`), so it is inert markup rather than paint work, and the page is
served from localhost. Dropping the arrows' class names saved 15 KB of it. If
Simon finds it heavy, the lever is capping voicings at two or three.

### Not yet done

- Simon has not looked at either feature in a browser.
- Auto-scroll was verified by simulating the real script against a stubbed DOM
  in node, not in a browser: speed arithmetic, mid-scroll speed change,
  re-anchoring after a manual scrollbar grab, stop-at-bottom, and clamping.
- The carousel CSS was reasoned through by hand, not rendered. The selector
  chain `input:nth-of-type(k):checked ~ span:nth-of-type(k)` depends on all
  radios preceding all panes, which the generated markup does.

## Known limits

- Scraping both sites breaks their ToS. Personal use, knowingly. Simon asked
  about shipping this to the Play Store on 2026-08-02 and decided against it:
  the lyrics are licensed content, UG pays for that licence and this app would
  not, and Play removes apps on a single valid notice.
- The chord-line test is a heuristic and only picks colour.
- UG's markup is unstable; re-check `wiki_tab.content` before debugging.
