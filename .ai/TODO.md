# TODO — BIBI-tabs

## Current Sprint

Phase 2 is written but **not yet run**. Everything below is about closing that gap
before starting Phase 3.

- [ ] Run `npm run dev`, click through the app, fix whatever is broken
- [ ] Check the player on an actual phone — flowing layout and tap targets
- [ ] Pinch-to-zoom on touch (buttons work; the gesture is not wired)
- [ ] Then Phase 3: `server/routers/proxy.py` with allowlist + private-IP refusal

---

## Phase 0 — Scaffold

- [x] Standalone git repo, `.gitignore` (node_modules, `__pycache__`, `.env`, `.svelte-kit`)
- [x] `app/` — `sv create`, TypeScript strict, vitest (unit only)
- [x] `app/` — `adapter-static` in SPA mode (`fallback: index.html`, `ssr = false`)
- [x] `app/` — vite dev proxy `/api` → `:8000`, so dev is same-origin too
- [x] `app/` — `@vite-pwa/sveltekit`, manifest, icons
- [x] `server/` — FastAPI + uvicorn skeleton, `/health`
- [x] `server/` — mount `app/build` at `/`, with SPA deep-link fallback
- [x] `server/schema.sql` — `song`, `setlist`, `setlist_song` with `owner_id` + `deleted_at`
- [x] `Dockerfile` **at the repo root** — multi-stage: node builds `app/`, python
      runs and serves it. Root, not `server/`, because the build context needs both.
- [x] `fly.toml` at the repo root (written, not deployed)
- [x] `README.md`

## Phase 1 — Music core + ChordPro + text parser

Pure logic, no I/O, written test-first. No `capo.ts`: capo is an annotation, not
arithmetic, so there is nothing to compute.

- [x] `music/chord.ts` — `parseChord("F#m7b5/A")` → `{root, quality, ext, bass}`
- [x] `music/spelling.ts` — sharp/flat choice from target key on circle of fifths
- [x] `music/transpose.ts` — `transpose(token, semitones, targetKey)`; `transposeKey`
- [x] `chordpro/parse.ts` — ChordPro text → AST (directives, comments, inline chords)
- [x] `chordpro/serialize.ts` — AST → ChordPro text (round-trip stable)
- [x] `import/text.ts` — chord-over-lyric → ChordPro (the ≥80% heuristic)
- [x] Fixtures + tests: instrumental lines, section headers, tabs vs spaces, overhang
- [x] Unit tests for all of the above, including enharmonic and slash-chord cases
      — 84 tests, `npm run check` clean, no `any`

## Phase 2 — Library + player ⭐

- [x] `music/key.ts` — guess song key from chord set (seeds the default display key)
- [x] `db/schema.ts` + `db/songs.ts` — Dexie tables mirroring the server schema
- [x] Library route: list, search by title/artist/lyrics, delete (soft)
- [x] Paste-in screen → parse → review → save
- [x] `components/ChordSheet.svelte` — flowing layout (chords above syllables)
- [x] Monospace layout mode + toggle
- [x] `components/Transposer.svelte` — key ± and a capo *number* (annotation only)
- [x] Lock/unlock: locked by default; unlock → raw ChordPro textarea in the stored key
- [x] Auto-save edits to IndexedDB (local write always succeeds; sync is separate)
- [x] Zoom: `A⁻ A⁺` buttons
- [x] Prefs split — `song.prefs` = `{transpose, capo}` (synced);
      `localStorage` = `{fontSize, layout}` (per-device, never synced)
- [x] Fingering dataset chosen: chords-db, **MIT verified**, vendored with its licence
- [x] `components/ChordDiagram.svelte` — SVG render, follows the displayed chord
- [x] Tap a chord → diagram sheet with alternate voicings
- [ ] **Pinch-to-zoom** — only the `A⁻ A⁺` buttons exist so far
- [ ] **Run the UI and fix what's broken.** 103 unit tests cover the pure logic;
      the Svelte components and IndexedDB wiring have never been executed.

## Phase 3 — Import

- [ ] `server/routers/proxy.py` — **domain allowlist + private-IP refusal in the same commit**
- [ ] `import/adapters/ug.ts` — page JSON blob → `[ch]…[/ch]` → ChordPro
- [ ] `import/adapters/boiteachansons.ts` — HTML → text → existing text parser
- [ ] `server/routers/search.py` — proxy each site's own search endpoint
- [ ] In-app search UI with per-source results (title, artist, rating, type)
- [ ] Import review screen (edit before committing to library)
- [ ] Settings toggle to disable scraping adapters

## Phase 4 — Sync + deploy

- [ ] `server/auth.py` — single `current_owner(request) -> owner_id` seam,
      bearer token from env, one constant owner
- [ ] `server/routers/songs.py` — GET list `?since=`, GET one, PUT upsert, DELETE (soft)
- [ ] `db/sync.ts` — push dirty, pull delta, last-write-wins on `updated_at`
- [ ] Sync status indicator + manual sync trigger; failure never blocks an action
- [ ] Neon database provisioned, schema applied
- [ ] `fly deploy`, HTTPS verified, static app served from the same origin
- [ ] Install PWA on phone and tablet, verify offline play

## Phase 5 — Later

- [ ] **Real user accounts** — `user` table + real `current_owner()` lookup.
      Additive by construction. Put `/api/proxy` and search behind the same seam.
- [ ] Capo as a transform — `shapes = sounding − capo` + a sounding/shapes toggle
- [ ] Inline chord editing in the rendered sheet (must shift by `−transpose` on save)
- [ ] Autoscroll — rAF loop, per-song speed, Screen Wake Lock (cheap; pull forward if wanted)
- [ ] Setlists — create, reorder, swipe between songs
- [ ] Ukulele + piano diagrams (renderer already takes a generic fingering shape)
- [ ] Export library as `.zip` of `.cho` files
- [ ] Print / PDF export
