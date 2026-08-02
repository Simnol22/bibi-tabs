# RELEVANT_STATE — BIBI-tabs

## Current State

**Phases 0 and 1 are done and committed.** Standalone git repo on `main`. The old
warning about being nested inside `sattt_db_utils` is resolved — git commands
here are safe.

- `app/` — SvelteKit + TS strict + vitest, `adapter-static` in SPA mode, PWA
  (manifest, service worker, generated icons). `npm run check` clean.
- `app/src/lib/music/` — `chord.ts`, `spelling.ts`, `transpose.ts`. Zero imports
  outside the folder, no `any`. **No `capo.ts`** — capo is an annotation.
- `app/src/lib/chordpro/` — `parse.ts`, `serialize.ts`. Byte-exact round trip on
  canonical text; messy input normalises once then holds.
- `app/src/lib/import/text.ts` — the ≥80% chord-line heuristic.
- `server/` — FastAPI, `/health`, static SPA mount with deep-link fallback,
  `schema.sql`. 3 pytest tests.
- Root `Dockerfile` (multi-stage) + `fly.toml`, written, never deployed.

84 vitest tests, 3 pytest tests, all green.

## In flight

Nothing. Next action is Phase 2 (see `TODO.md` → Current Sprint), which is the
first phase with a UI.

## Open decisions

- **Fingering dataset.** Leading candidate `tombatossals/chords-db` (also covers
  ukulele). **Licence unverified** — check before bundling. Alternatives:
  `szaza/guitar-chords-db-json` (99k chords, probably too many), ChordPro's own
  bundled definitions. Decide before Phase 2.

## Decisions made while building Phase 1

- **`transpose(token, semitones, targetKey) -> string`**, strings in and out,
  rather than passing `Chord` objects around. The renderer holds raw ChordPro
  tokens, so this is what it actually needs, and an unparseable token (`N.C.`,
  a repeat mark) passes through untouched instead of being mangled. `Chord`
  stays an implementation detail of `chord.ts`.
- **Spelling stops at the twelve practical note names.** Pitch 11 in Gb major
  comes back as `B`, not the theoretically correct `Cb`. Confirmed with Simon.
  Pinned by a test so it reads as a decision, not an oversight.
- **The slash bass is spelled by key signature**, same rule as the root — so
  `F#m7b5/A` +1 into G major gives `A#` where a theorist writes `Bb`. Passing
  the key the song is actually in (Gm) gives `Bb`. Also confirmed and pinned.
- **`quality` and `ext` are opaque text.** Only root and bass carry pitch, so
  transposition never has to understand `7b5` — and a sheet reads back exactly
  as written.
- **`parseChord` returning null is load-bearing**, not defensive: the chord-line
  heuristic counts surviving tokens. Hence the tests asserting that `Chorus`,
  `Bass`, `Dad`, and solfège are *not* chords.
- **Chord-only lines pad to their original columns** rather than collapsing to
  single spaces — on an instrumental line the width of a gap is the timing.
- **`[Chorus]` becomes `{comment: Chorus}`** on import. Passing it through would
  make ChordPro read it as a chord named "Chorus" — corruption, not ugliness.
- **Tabs expand at 8 columns before pairing**, since a chord finds its syllable
  by column index.

## Decisions made this session (2026-08-01, second pass)

- **Hosting: one Fly app.** `adapter-static`; FastAPI serves the build at `/` and
  the API at `/api`. One domain, one deploy, no CORS. Rejected: a separate static
  host (two deploys to keep in step, CORS on every route) and `adapter-node` (a
  second runtime rendering pages with no data, since the library lives in the
  browser). Dockerfile is multi-stage — node builds `app/`, python runs it.

- **Capo is an annotation, not a transform.** Transpose is the only thing that
  moves chords; capo is a number printed at the top of the sheet, the way a paper
  sheet says "Capo 3". This relaxes the old invariant 3. Accepted cost: the app
  can't say "capo 3, play G shapes" for a song stored in Bb — you set transpose
  −3 and note the capo yourself, and the screen ends up identical. Cheap to
  upgrade later (same primitive, minus sign), so it stays in Phase 5.
  Consequence: **`music/capo.ts` no longer exists** — there is no arithmetic.
- **Lock/edit added.** Sheet is locked by default. Unlock reveals the **raw
  ChordPro source in the stored key** in a textarea — chord changes, placement,
  add/remove, structure, all as text, no bespoke editing UI. Chosen over
  tap-a-chord-to-edit specifically because editing a *transposed* view and
  writing it back silently re-keys the song. Editing raw source in the original
  key makes that unrepresentable. Inline editing is Phase 5 and must shift by
  `−transpose` on save.
- **Offline scope narrowed to what's true.** Library and player never touch the
  network; search and sync are online features that degrade rather than block.
  Auto-save writes to IndexedDB immediately and syncs in the background, so a
  local write always succeeds.
- **Prefs split by what the state is about.** `song.prefs = {transpose, capo}`
  syncs; `{fontSize, layout}` lives in `localStorage` and never syncs — syncing
  font size between a phone and a laptop would be actively wrong. Zoom control
  (`A⁻ A⁺` + pinch) added.
- **Multi-account promoted from hypothetical to planned direction.** Other people
  eventually get accounts on the same server with their own private libraries.
  Not built now; the only concessions are `owner_id` on every row and a single
  `current_owner()` auth seam. No `user` table yet. Noted: once multi-account
  exists, `/api/proxy` and search must sit behind the same seam.
- **Text parser moved to Phase 1**, resolving a contradiction — `ARCHITECTURE.md`
  called it "the foundation, not a fallback" while `TODO.md` had it in Phase 2.
  It's pure, I/O-free and edge-case-heavy, same as the rest of Phase 1.
- **`music/key.ts` moved to Phase 2** — nothing consumes it until the player
  needs a default key, so writing it in Phase 1 would be building ahead of need.

## Decisions from the first planning session (2026-08-01)

Still standing, condensed: PWA over Flutter; SvelteKit over React; self-hosted on
Fly.io + Neon rather than Supabase; URL importer included despite the UG ToS
caveat (isolated adapters, disable toggle, mandatory review screen); in-app
search hits each site's own endpoint rather than Google; paste-text parser is
infrastructure, not a feature; autoscroll deferred to Phase 5.

## Known issues / gotchas

- `/api/proxy` is an SSRF hole without a domain allowlist and private-IP refusal.
  Same-commit requirement, not a follow-up.
- UG's page structure (JSON blob, `[ch]…[/ch]`) is accurate as of planning but
  unverified against a live page. Confirm before building the adapter.
- Dev runs vite on `:5173` and FastAPI on `:8000` — cross-origin unless the vite
  dev proxy forwards `/api` to `:8000`. Set that up in Phase 0 so dev matches
  production.
