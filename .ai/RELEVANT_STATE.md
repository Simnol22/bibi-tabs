# RELEVANT_STATE — BIBI-tabs

## Current State

**V1 works.** Fetches a live Ultimate Guitar page, saves it, opens it with the
chords in the right columns. Verified end to end, not just by unit test.

```
bibi <ug-url>   →  ~/.bibi-tabs/oasis-wonderwall.txt  +  a browser tab
```

26 tests pass, no network needed. conda env `bibi-tabs` (python 3.11), zero
dependencies.

## In flight

Nothing. Waiting on Simon using it on real songs.

## The rewrite (2026-08-02)

The SvelteKit PWA + FastAPI backend was deleted and replaced with ~300 lines of
Python. Simon's call: too complicated, too many features, and the one thing he
wanted — a UG link opening as a readable sheet — was the one thing it couldn't
do. Everything is preserved in git history:

| | |
|---|---|
| `f0646e4` | Phase 0 scaffold |
| `5d438cf` | music theory + ChordPro, 84 tests — port from here if transposition is ever wanted |
| `8ed0bb1` | library, player, chord diagrams; includes the vetted MIT chords-db dataset |

The constraint that settled it: **a browser cannot fetch a UG page** (CORS), so
the web version needed a server running purely to read a link. Python doesn't.

## Verified against a live page (2026-08-02)

Worth re-checking before debugging anything UG-related, since this is the part
that rots:

- Sheet lives at `store.page.data.tab_view.wiki_tab.content`, inside an
  HTML-escaped JSON blob in `<div class="js-store" data-content="…">`.
- Metadata: `data.tab.song_name` / `.artist_name` / `.tonality_name`, and
  `data.tab_view.meta.capo` / `.tuning`.
- Chords are `[ch]…[/ch]`; aligned sections are wrapped in `[tab]…[/tab]`.
- **Markers overlay already-aligned text.** Confirmed on a real page: chords at
  columns 0, 5, 9, 13 above a 19-character lyric line, unchanged after
  stripping. So the renderer never adjusts spacing.
- Line endings are CRLF.

## Decisions worth keeping

- **One code path for chord lines.** UG's `[ch]` markers would identify chord
  lines perfectly, but a saved file no longer has them. Rather than one rule at
  fetch and another at load, everything uses the ≥80% heuristic. It only picks
  colour, so being wrong is cosmetic.
- **Saved files are clean text, not ChordPro.** Readable and hand-editable; a
  file Simon writes himself renders the same as a fetched one.
- **`~/.bibi-tabs/`, not the repo.** Songs are copyrighted; they should not end
  up in git.
- **No abstract `Source` base class.** There is one source. `UltimateGuitar` has
  a `matches()` method, which is all the shape a second one would need.

## Known limits

- `[tab]` blocks holding riff notation rather than chords render as-is. Fine,
  but untested against a tab-heavy song.
- A chord line whose chords run past the end of the lyric is untested.
- Only Ultimate Guitar. Boîte à Chansons was in the old plan and is not here.
