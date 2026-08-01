# TODO — BIBI-tabs

## Current Sprint

- [x] Move `bibi-tabs/` out of the nested `sattt_db_utils` repo and `git init` it standalone
- [ ] Phase 0: scaffold SvelteKit + TS strict + vitest in `app/`
- [ ] Phase 0: scaffold FastAPI skeleton + `schema.sql` in `server/`
- [ ] Phase 1: `music/chord.ts` — parse chord symbols, test-first
- [ ] Phase 1: `music/transpose.ts` + `music/spelling.ts` — shift + enharmonics

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

- [ ] `music/chord.ts` — `parseChord("F#m7b5/A")` → `{root, quality, ext, bass}`
- [ ] `music/spelling.ts` — sharp/flat choice from target key on circle of fifths
- [ ] `music/transpose.ts` — shift a parsed chord by N semitones; `transposeKey`
- [ ] `chordpro/parse.ts` — ChordPro text → AST (directives, sections, inline chords)
- [ ] `chordpro/serialize.ts` — AST → ChordPro text (round-trip stable)
- [ ] `import/text.ts` — chord-over-lyric → ChordPro (the ≥80% heuristic)
- [ ] Fixtures + tests: instrumental lines, section headers, tabs vs spaces, overhang
- [ ] Unit tests for all of the above, including enharmonic and slash-chord cases

## Phase 2 — Library + player ⭐

- [ ] `music/key.ts` — guess song key from chord set (seeds the default display key)
- [ ] `db/schema.ts` — Dexie tables mirroring the server schema
- [ ] Library route: list, search by title/artist/lyrics, delete (soft)
- [ ] Paste-in screen → parse → review → save
- [ ] `components/ChordSheet.svelte` — flowing layout (chords above syllables)
- [ ] Monospace layout mode + toggle
- [ ] `components/Transposer.svelte` — key ± and a capo *number* (annotation only)
- [ ] Lock/unlock: locked by default; unlock → raw ChordPro textarea in the stored key
- [ ] Auto-save edits to IndexedDB (local write always succeeds; sync is separate)
- [ ] Zoom: `A⁻ A⁺` and pinch
- [ ] Prefs split — `song.prefs` = `{transpose, capo}` (synced);
      `localStorage` = `{fontSize, layout}` (per-device, never synced)
- [ ] Pick a fingering dataset + **verify its licence** before bundling
- [ ] `components/ChordDiagram.svelte` — SVG render, follows the displayed chord
- [ ] Tap a chord → diagram sheet with alternate voicings

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
