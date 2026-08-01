# plan.md — BIBI-tabs

## Goal

One personal library of guitar chord sheets, imported from the web, stored in an
open format, playable ad-free on laptop, phone and tablet — online or off.

**Definition of done for v1:** Simon can search a song by name inside the app,
import it in one tap, and play it on his phone at a campfire with no signal, in
whatever key suits his voice, tapping any chord he doesn't know to see the
fingering.

## Principles

1. **Own the data.** ChordPro, an open standard, exportable at any time. The app
   being abandoned must not cost you the library.
2. **Offline is the baseline, not a feature.** You play guitar in places with no
   signal.
3. **Smallest thing that works.** A personal tool that stays hackable for years
   beats a feature-complete one you can't read.
4. **Risky parts last.** Scraping breaks; the app must already be useful without it.

## Methodology

Each phase ends at a point where stopping would be reasonable. Pure logic
(music theory, parsers) is written test-first — it has nasty edge cases and no
I/O, which is exactly where tests pay. UI is written by hand against real songs,
not mocked fixtures.

## Modules

| Module | Location | Responsibility |
|---|---|---|
| **music** | `app/src/lib/music/` | Chord symbol parsing, transposition, enharmonic spelling, key detection. Pure, zero deps. No capo maths — capo is an annotation. |
| **chordpro** | `app/src/lib/chordpro/` | ChordPro text ⇄ AST. Directives, sections, inline chords. |
| **import** | `app/src/lib/import/` | Chord-over-lyric text parser + one adapter file per site. Everything outputs ChordPro. |
| **db** | `app/src/lib/db/` | Dexie schema, CRUD, sync engine (push dirty / pull delta, LWW). |
| **components** | `app/src/lib/components/` | ChordSheet renderer, ChordDiagram SVG, Transposer, library list. |
| **server** | `server/` | Songs CRUD + delta endpoint, allowlisted fetch proxy, per-site search proxy. |

## Milestones

### Phase 0 — Scaffold
SvelteKit + TS + vitest, FastAPI skeleton, `schema.sql`, Dockerfile + `fly.toml`
written but unused. Nothing deployed.

### Phase 1 — Music core + ChordPro + text parser
`music/` (chord, spelling, transpose), `chordpro/` (parse, serialize) and
`import/text.ts` (chord-over-lyric → ChordPro) complete and fully unit-tested.
No UI. This is the foundation everything else assumes is correct.

The text parser lives here rather than with the import UI because it is pure,
I/O-free, edge-case-heavy logic — the same profile as the rest of Phase 1. That
leaves Phase 2 as purely UI and storage.

`music/key.ts` is *not* here: nothing consumes it until the player needs a
default key, so it moves to Phase 2 rather than being built ahead of need.

### Phase 2 — Library + player ⭐
The app becomes genuinely useful. Paste a song → it's in the library → open it →
transpose it → note a capo → unlock and fix a wrong chord → tap a chord for its
diagram. All local, all offline, no server involved. **If the project stalled
here it would still be worth having.**

Includes `music/key.ts` (default key detection), the lock/edit flow, and zoom.

### Phase 3 — Import
Fetch proxy (with allowlist), UG adapter, Boîte à Chansons adapter, in-app
search across sources, import review screen. One-tap song acquisition.

### Phase 4 — Sync + deploy
Backend CRUD + delta, sync engine, deploy to Fly, install the PWA on phone and
tablet. Library becomes shared across devices.

### Phase 5 — Later
**Real user accounts** — a planned direction, not a maybe: other people get an
account on the same server, each with their own private library. Additive by
construction (a `user` table + a real `current_owner()` lookup), which is the
entire reason `owner_id` and the auth seam exist from Phase 0.

Also: autoscroll (cheap — rAF loop + Screen Wake Lock; pull forward if wanted),
setlists, ukulele/piano diagrams, PDF/print export, capo-as-transform with a
sounding/shapes toggle, inline chord editing.

## Explicit non-goals

- Audio playback, backing tracks, or tempo/click.
- Tab (six-string notation) rendering. Chords over lyrics only.
- Sharing songs *between* accounts, public libraries, or social features.
  Multi-account means several private libraries on one server — nothing more.
- Native App Store distribution.
- Editing songs collaboratively.
