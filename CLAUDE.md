# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project

**BIBI-tabs** — an ad-free, offline-first guitar chord sheet library and player.
Import songs from Ultimate Guitar / Boîte à Chansons, store them once, play them
on desktop, phone or tablet with transposition, capo, and chord diagrams.

Read `ARCHITECTURE.md` first — it explains *why* the design is what it is. Read
`.ai/RELEVANT_STATE.md` to find out what is currently in flight.

## Stack

- **`app/`** — SvelteKit + TypeScript, built as an installable PWA. Nearly all
  logic lives here.
- **`server/`** — FastAPI + Postgres (Neon), deployed on Fly.io. Sync API and a
  fetch proxy. Deliberately thin.
- Local storage: IndexedDB via `dexie`. Tests: `vitest` (app), `pytest` (server).
- **One deploy, one origin.** `app/` builds to static files (`adapter-static`)
  which FastAPI serves at `/`. There is nothing to server-render — the library
  lives in the browser. Same origin means the sync API needs no CORS.

## Commands

```bash
# Frontend
cd app && npm install
npm run dev                  # dev server on :5173
npm run test                 # vitest
npm run test -- --watch
npm run build && npm run preview

# Backend
cd server && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
pytest

# Deploy — from the repo root; the Dockerfile needs both app/ and server/
fly deploy
```

## Non-negotiable invariants

These are the rules that keep the design coherent. Breaking one is a bug even if
the tests pass.

1. **ChordPro is the single source of truth.** A song is stored once, in its
   original key. Transposition and layout are *display-time* transforms; capo is
   an annotation (see 3). Never write a transposed version back into the stored
   `chordpro` — including when saving an edit made while the view is transposed.
2. **`app/src/lib/music/` is pure.** No DOM, no network, no storage, no
   dependencies. Every function is deterministic and unit-tested. This is the
   part that has to be *correct*.
3. **Transpose moves chords; capo does not.** `displayed = stored + transpose`,
   computed at display time. `capo` is a per-song number printed at the top of
   the sheet — an annotation, not a transform. Chord diagrams follow the
   *displayed* chords. (The full `shapes = sounding − capo` model with a
   sounding/shapes toggle is deliberately deferred. It is the same primitive with
   a minus sign, so adding it later stays additive — but do not conflate the two
   in the meantime; that's the classic bug in this domain.)
4. **The library and player are offline-first.** Browsing, opening, playing,
   transposing and editing read and write IndexedDB directly and never await the
   network. Search and sync are *online* features: they may fail, and must
   degrade rather than block. A local write always succeeds and syncs later.
5. **Deletes are soft.** `deleted_at` tombstones, always. A hard delete
   resurrects itself on the other device's next sync.
6. **The proxy allowlist ships with the proxy.** `GET /api/proxy?url=` is an
   SSRF hole without a domain allowlist and a private-IP-range refusal. These are
   not a follow-up commit.
7. **Site adapters are one file each**, under `app/src/lib/import/adapters/`.
   Site-specific selectors, regexes and JSON paths never leak outside them.
   Scraped imports always land in a review screen before entering the library.
8. **The sheet is locked by default, and edits are stored in the original key.**
   Unlocking edits the ChordPro source. Never write a *displayed* chord back to
   storage — if inline editing is ever added to a transposed view, the edit is
   shifted by `−transpose` first. Otherwise editing silently re-keys the song.
9. **`owner_id` on every user-owned row, and exactly one auth seam.**
   Multi-account is a planned direction, not a hypothetical. All ownership
   resolution goes through a single `current_owner()` on the server, so swapping
   the shared bearer token for real accounts touches one file, not every query.

## Code style

**Minimalism is critical.** No extra function, no code for hypothetical future
behaviour. One function does one thing. The smallest possible footprint for the
largest feature set — that is what keeps this readable in two years.

- Small pure functions over classes, except where state genuinely clusters
  (the sync engine, the IndexedDB store).
- Write the music-theory and parser code **test-first**. It's pure logic with
  nasty edge cases; that's exactly where tests pay for themselves.
- TypeScript strict mode. No `any` in `lib/music/` or `lib/chordpro/`.
- Prefer a Svelte store over prop-drilling for player state (key, capo, font).

## Known gotchas

- **Enharmonic spelling** must be derived from the target key's position on the
  circle of fifths, not a fixed sharp/flat table — otherwise transposed sheets
  read wrong (`Gb` where `F#` belongs).
- **The chord-line heuristic** (≥80% of tokens parse as chords) has real edge
  cases: instrumental lines with no lyric beneath, section headers like
  `[Chorus]`, tabs vs spaces, chords positioned past the end of the lyric line.
  Add a fixture, don't patch the regex blindly.
- **UG's markup will break.** The tab body currently lives in a JSON blob on the
  page using `[ch]…[/ch]` markers. Treat the exact path as unverified at any
  given moment; confirm against a live page before debugging further.
- **Editing while transposed re-keys the song** if you write the displayed chord
  back. Phase 2 sidesteps this: unlock reveals the raw ChordPro in the *stored*
  key, so an edit is by construction an edit to the source of truth.
- **iOS PWA storage is evictable.** Never treat IndexedDB as durable — the server
  is the backup, and until Phase 4 exists, export matters.
- **Screen Wake Lock** needs a user gesture and is released when the tab
  backgrounds. Re-acquire on `visibilitychange`.

## Context files

`.ai/` holds `AI_CONTEXT.md`, `plan.md`, `TODO.md`, `RELEVANT_STATE.md`. Keep
them current as a routine part of every session — no need to ask first. Reset
`RELEVANT_STATE.md` to a stub after every `git push`; the commit history is the
permanent record.
