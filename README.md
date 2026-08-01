# BIBI-tabs

An ad-free, offline-first guitar chord sheet library and player. Import songs
once, own them forever, play them on laptop, phone or tablet from the same
library — with transposition, chord diagrams, and no signal required.

Songs are stored exactly once, as **ChordPro**, in their original key. Everything
else — transposition, layout, font size — is computed at display time. The format
is open and 40 years old, so the library outlives the app.

> **Status: Phase 0.** Scaffolding only. See [`.ai/TODO.md`](.ai/TODO.md) for the
> build order and [`ARCHITECTURE.md`](ARCHITECTURE.md) for why the design is what
> it is.

## Layout

```
app/        SvelteKit PWA — music theory, ChordPro, storage, UI. Nearly all the logic.
server/     FastAPI — sync API + fetch proxy, and it serves the built app. Thin on purpose.
Dockerfile  Builds both halves into one image.
fly.toml    Deploy config. Written, not deployed.
.ai/        Working context files (see CLAUDE.md).
```

The app builds to static files that FastAPI serves at `/`, so there is **one Fly
app, one domain, one deploy, and no CORS**. There is nothing to server-render —
the library lives in IndexedDB in the browser.

## Running it

Two processes in dev. Vite proxies `/api` to the backend, so dev is same-origin
just like production.

```bash
# frontend — http://localhost:5173
cd app
npm install
npm run dev

# backend — http://localhost:8000
cd server
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload --port 8000
```

The backend is optional until Phase 4. The app works entirely offline without it.

## Tests

The music theory and parsers are written test-first — they are pure logic with
nasty edge cases, which is exactly where tests pay for themselves.

```bash
cd app    && npm run test          # vitest;  -- --watch to iterate
cd server && .venv/bin/python -m pytest
```

## Deploying

Not yet done. When it is, from the repo root:

```bash
fly deploy
```

The Dockerfile builds the PWA with Node, then copies the output into a Python
image that serves it alongside the API.
