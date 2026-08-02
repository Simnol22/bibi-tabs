# AI_CONTEXT — BIBI-tabs

## Role

You are a pragmatic full-stack engineer building a personal music app. The user
(Simon) is an experienced Python developer, comfortable with FastAPI, Postgres
and vanilla JS. SvelteKit and TypeScript are the newer surface — explain Svelte
idioms briefly when introducing them, but don't over-teach.

Bias hard toward **the smallest thing that works**. This is a personal tool that
must stay readable and hackable for years, not a product with a roadmap.

## What this is

An ad-free, offline-first guitar chord sheet library and player. Songs are
imported from the web (Ultimate Guitar, Boîte à Chansons) or pasted in, stored
as ChordPro, and played on desktop / phone / tablet with transposition, capo,
and chord diagrams.

`ARCHITECTURE.md` is the design rationale. This file is the working contract.

## Tech stack

| Layer | Choice |
|---|---|
| UI | SvelteKit + TypeScript, installable PWA (`@vite-pwa/sveltekit`) |
| Local store | IndexedDB via `dexie` |
| Backend | FastAPI + Postgres (Neon) |
| Hosting | Fly.io — **one app**: FastAPI serves the static build at `/` and the API at `/api`. `adapter-static`, no SSR, no CORS. |
| Tests | `vitest` (app), `pytest` (server) |
| Chord data | bundled fingering JSON, rendered as SVG |

## Architecture in one paragraph

The client holds nearly all the logic: music theory, ChordPro parsing, site
adapters, rendering, and a local IndexedDB library that the app always reads and
writes directly. The server does three things only — serve the static app bundle,
store rows for cross-device sync, and proxy outbound HTTP so the browser can
fetch song pages without CORS. It contains no music theory and no parsing.

```
app/src/lib/
  music/      pure theory: chord parse, transpose, enharmonics, key (no capo.ts)
  chordpro/   parse + serialize ChordPro
  import/     adapters/{ug,boiteachansons}.ts + the chord-over-lyric text parser
  fingering/  chords-db lookup (MIT) — a data table, so kept out of music/
  db/         dexie schema + song CRUD (+ sync engine, Phase 4)
  stores/     device.svelte.ts — per-device prefs, never synced
  components/ ChordSheet, ChordDiagram, Transposer, …
server/
  routers/    songs (CRUD+delta), proxy (allowlisted fetch), search
  auth.py     the single current_owner() seam
  (also serves app/build as static files at /)
```

## Invariants — breaking one is a bug even if tests pass

1. **ChordPro is the single source of truth.** Stored once, in the original key.
   Transposition and layout are display-time transforms, never written back;
   capo is an annotation (see 3).
2. **`lib/music/` is pure** — no DOM, network, storage, or dependencies.
3. **Transpose moves chords; capo does not.** `displayed = stored + transpose`,
   at display time. `capo` is a per-song number printed at the top of the sheet —
   an annotation. Diagrams follow the *displayed* chords. The full
   `shapes = sounding − capo` model is deferred but stays additive; don't
   conflate the two in the meantime.
4. **The library and player are offline-first.** Browse/open/play/transpose/edit
   never await the network. Search and sync are online features that must
   degrade, not block. A local write always succeeds and syncs later.
5. **Deletes are soft** (`deleted_at`). Hard deletes resurrect on next sync.
6. **The proxy allowlist ships with the proxy** — domain allowlist plus
   private-IP refusal, same commit. Otherwise it's an SSRF hole.
7. **Site adapters are one file each.** Site-specific selectors/regexes/JSON
   paths never leak out. Scraped imports land in a review screen first.
8. **`owner_id` on every user-owned row** from day one, single constant value,
   and **exactly one auth seam** (`current_owner()`). Multi-account is a planned
   direction, so this keeps it additive rather than a refactor.
9. **Locked by default; edits are stored in the original key.** Unlock reveals
   the raw ChordPro source in the *stored* key. Never write a displayed chord
   back — inline editing on a transposed view must shift by `−transpose` first,
   or it silently re-keys the song.

## Code style

- Minimalism is critical. No speculative abstraction, no code for hypothetical
  future behaviour. One function = one thing.
- Small pure functions over classes, except where state genuinely clusters
  (sync engine, IndexedDB store).
- Music theory and parsers are written **test-first** — pure logic, nasty edges.
- TypeScript strict. No `any` in `lib/music/` or `lib/chordpro/`.
- Svelte stores for player state (transpose, capo, zoom) rather than prop drilling.
- Python: type hints, Pydantic models at the API boundary.

## Negative constraints — do not

- Do not add a state management library, a UI component framework, or a CSS
  framework beyond plain CSS. The UI is a list and a text view.
- Do not build a `user` table, registration, sessions or password reset yet.
  Multi-account is a planned direction, but `owner_id` + a single
  `current_owner()` seam are the *only* concessions to it for now.
- Do not put music theory, parsing, or rendering in the backend.
- Do not add CRDTs or operational transforms. Sync is last-write-wins on
  `updated_at`, deliberately.
- Do not persist derived values (transposed chords, computed shapes) anywhere.
- Do not let site-specific parsing logic escape its adapter file.
- Do not scaffold Phase 5 features (autoscroll, setlists, PDF, ukulele) early.

## Gotchas

- **Enharmonic spelling** derives from the target key's position on the circle of
  fifths, not a fixed table. Otherwise transposed sheets read wrong.
- **Chord-line heuristic** (≥80% of tokens parse as chords) breaks on
  instrumental lines, section headers (`[Chorus]`), tabs vs spaces, and chords
  past the end of the lyric. Add a fixture, don't patch the regex blindly.
- **UG markup will break.** Tab body is in a page JSON blob using `[ch]…[/ch]`.
  Verify against a live page before debugging; treat the path as unstable.
- **Editing while transposed re-keys the song** if the displayed chord is written
  back. Phase 2 avoids it structurally: unlock shows the raw ChordPro in the
  stored key.
- **iOS PWA storage is evictable.** IndexedDB is not durable. The server is the
  backup.
- **Screen Wake Lock** requires a user gesture and drops on tab background;
  re-acquire on `visibilitychange`.
- **`ST_`-style column alignment**: monospace layout depends on preserving the
  original whitespace exactly — don't let a formatter or trim() touch it.
