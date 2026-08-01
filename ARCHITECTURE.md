# BIBI-tabs — Architecture

An ad-free, offline-first chord sheet library and player. Import songs from the
web once, own them forever, play them on laptop, phone or tablet from the same
library.

---

## 1. The one idea that shapes everything

**Every song is stored exactly once, as ChordPro text, in the original key.**

Everything else — transposition, capo, chord diagrams, font size, layout — is a
*rendering decision* computed at display time from that single source of truth.
Nothing derived is ever persisted into the song body.

```
stored:    [F]Yester[Em7]day, [A7]all my [Dm]troubles seemed so far a[Bb]way
                    │
                    ├── display in G (+2)      →  [G]Yester[F#m7]day, [B7]all my...
                    ├── display in D (−3)      →  [D]Yester[C#m7]day, [F#7]all my...
                    └── diagram for Em7        →  0 2 0 0 0 0
```

This is why the format matters. ChordPro is an open, human-readable, 40-year-old
standard: it imports and exports cleanly, survives this app being abandoned, and
is diffable in git. It also cleanly separates *chords* from *lyrics*, which
column-aligned text does not — and that separation is what makes responsive
mobile layout possible at all.

---

## 2. Stack

| Layer | Choice | Why |
|---|---|---|
| UI | **SvelteKit + TypeScript**, built as a **PWA** | One codebase for desktop/phone/tablet. Installs to home screen and dock. Smallest bundle and fastest render of the options — matters for smooth scrolling on a phone. |
| Local storage | **IndexedDB** (via `dexie`) | Full library available offline. The app must work with no signal, in a basement, at a campfire. |
| Backend | **FastAPI + Postgres (Neon)** | Sync only. Deliberately thin. Reuses a stack you already run. |
| Hosting | **Fly.io**, one app | Free TLS + subdomain (a PWA *requires* HTTPS to install), push-to-deploy, isolated from your work infra. |
| Chord data | **Bundled JSON fingering DB** → rendered as SVG | Works offline, no image assets, no network on tap. |

### One deploy, one origin

`app/` builds to **static files** (`adapter-static`) and FastAPI serves them at
`/`, alongside `/api/…`. A single Fly app, a single domain, a single
`fly deploy`.

Server-side rendering would buy nothing here: the library lives in IndexedDB *in
the browser*, and so do the music theory and the renderer. The server has no
data to render a page with, so paying for a second runtime (Node beside Python)
to serve empty shells is pure cost. Static also means the app is a plain folder
of files — trivially cacheable by the service worker, and trivially hostable
anywhere else if Fly ever falls through.

The quiet win is CORS: same-origin app and API means there is none to configure.
(The fetch proxy in §4 exists for a different reason — *outbound* CORS when
scraping other sites.)

### Repo layout

```
bibi-tabs/
├── app/                     # SvelteKit PWA — where nearly all the logic lives
│   ├── src/lib/
│   │   ├── music/           # pure music theory. zero deps, zero I/O, 100% tested
│   │   ├── chordpro/        # ChordPro parse + serialize
│   │   ├── import/          # source adapters (UG, Boîte à Chansons, plain text)
│   │   ├── db/              # IndexedDB store + sync engine
│   │   └── components/      # ChordSheet, ChordDiagram, Transposer, …
│   └── src/routes/          # /  /song/[id]  /import  /settings
├── server/                  # FastAPI — sync API, fetch proxy, serves the built app
│   └── main.py  routers/  models.py  schema.sql
├── Dockerfile               # builds both halves into one image — context is the root
├── fly.toml
├── .ai/                     # AI context files (see CLAUDE.md)
└── ARCHITECTURE.md
```

**The weight is deliberately in the client.** The server stores rows and forwards
HTTP requests. It contains no music theory, no parsing, and no rendering. That
keeps one language for all the interesting logic, keeps it unit-testable without
a database, and means the app is fully functional before the backend exists.

---

## 3. The music core (`app/src/lib/music/`)

Pure functions. No DOM, no network, no storage. This is the part that must be
*correct*, so it's the part that gets written test-first.

```
chord.ts       parse "F#m7b5/A" → { root:'F#', quality:'m', ext:'7b5', bass:'A' }
transpose.ts   shift a parsed chord by N semitones
spelling.ts    choose F# vs Gb based on the target key
key.ts         guess a song's key from its chord set        (Phase 2)
```

There is no `capo.ts`. Capo is an annotation printed at the top of the sheet, not
arithmetic — see §5.

### Transposition and capo — the subtle part

These are two different things, and conflating them is the classic bug in this
domain. They are worth keeping straight even though only one of them currently
computes anything:

- **Transpose** changes what the song *sounds like*. Song stored in C, you pick
  D → everything shifts +2 semitones. This is implemented.
- **Capo** changes what you *finger* while the sound stays put. Song in D with
  capo 2 → you play C shapes, and it still sounds like D. This is **not**
  implemented as a transform; the app just records and prints the number.

The full model, deferred to Phase 5:

```
sounding = stored + transpose          ← what the audience hears
shapes   = sounding − capo             ← what your fingers do
```

Today only the first line exists, and it is what gets printed. Adding the second
is the same primitive with a minus sign, which is why deferring it is safe — but
it is also why the two must never be collapsed into one knob in the meantime.

### Enharmonic spelling

`C# major` and `Db major` are the same pitches and very different to read.
Spelling is chosen from the target key's position on the circle of fifths —
sharp keys get sharps, flat keys get flats — not by a fixed lookup table. Getting
this wrong is what makes transposed sheets on other apps look wrong.

---

## 4. Getting songs in (`app/src/lib/import/`)

Three sources, one interface, one output format:

```
       ┌──────────────┐
URL ──▶│  ug adapter  │──┐
       └──────────────┘  │
       ┌──────────────┐  │
URL ──▶│ boiteachans. │──┼──▶ ChordPro ──▶ review screen ──▶ library
       └──────────────┘  │      text        (edit before
       ┌──────────────┐  │                   committing)
text ─▶│ text parser  │──┘
       └──────────────┘
```

```ts
interface SourceAdapter {
  matches(url: string): boolean
  search(query: string): Promise<SearchResult[]>
  parse(raw: string): Song          // → { title, artist, chordpro }
}
```

Each site is **one file**. When Ultimate Guitar redesigns — and it will — you fix
`ug.ts` and nothing else moves.

### The text parser is the foundation, not a fallback

Everything eventually funnels through the chord-over-lyric parser, so it gets
built first and tested hardest. It takes the universal format:

```
C          G         Am        F
Yesterday, all my troubles seemed so far away
```

and produces `[C]Yesterday, [G]all my [Am]troubles seemed so far a[F]way`.

The heuristic: a line is a **chord line** if it's non-empty and ≥80% of its
whitespace-separated tokens parse as valid chord symbols. Pair it with the
following line and map each chord's *column index* to a character offset in the
lyric. Edge cases that need tests: chord lines with no lyric under them
(instrumental breaks), lyric lines with no chords, section headers
(`[Chorus]`, `Verse 1:`), tabs vs spaces, and lines where the chord sits past
the end of the lyric.

This single function makes the app work with *any* site, forever, via copy-paste
— which is the insurance policy behind the scraping adapters.

### Search

In-app search hits **each site's own search endpoint** through the proxy, not a
general web search. UG's search returns the same JSON structure the importer
already parses, so results come back with title, artist, rating, and type
(chords / tab / ukulele) — far better signal than ten blue links, and no API key
to manage. Results render as a list; tap one to import it.

A generic web-search source (Brave API or Google CSE) is a later add-on if you
want to reach sites without adapters.

### ⚠️ Standing caveat on the URL importer

Scraping Ultimate Guitar violates their Terms of Service. You've made that call
knowingly for personal use, so the plan includes it — but the design treats it as
**load-bearing-but-untrusted**:

- It is isolated in `import/adapters/`, toggleable off in settings.
- It will break on their next redesign. Expect it, budget for it.
- Every imported song lands in a **review screen** before entering the library,
  so a broken parse is visible immediately rather than silently corrupting things.
- Paste-text always works and needs no adapter.

### ⚠️ The proxy is the one real security hole

`GET /api/proxy?url=…` fetches arbitrary URLs *from your server*. Unrestricted,
that's a textbook SSRF: anyone who finds it can make your Fly machine hit your
internal network or cloud metadata endpoints. **The domain allowlist is not
optional and not a "later" item** — it ships in the same commit as the endpoint,
and the endpoint refuses anything that resolves to a private IP range.

---

## 5. The player

```
┌──────────────────────────────────────┐
│  Yesterday · The Beatles         🔒  │
│  Key [F ▾]  −  +    Capo 3     A⁻ A⁺ │
├──────────────────────────────────────┤
│   F        Em7    A7      Dm         │  ← tap any chord → diagram sheet
│  Yesterday, all my troubles seemed…  │
│                                      │
│   Bb       C7      F                 │
│  Now it looks as though they're here │
└──────────────────────────────────────┘
```

### The two knobs

- **Transpose** is the only thing that moves chords. `displayed = stored +
  transpose`, recomputed on every render, never written back.
- **Capo** is an *annotation* — a number printed at the top of the sheet, the way
  a paper chord sheet says "Capo 3". It does not shift anything.

These are deliberately not the same mechanism, and the docs keep them apart even
though only one of them currently does arithmetic. The richer model — `sounding =
stored + transpose`, `shapes = sounding − capo`, with a toggle for which is
printed — is **deferred, not rejected**. It is the same primitive with a minus
sign, so it stays a purely additive change. What it would buy: the app could
answer *"capo 3 and play G shapes"* for a song stored in Bb, instead of you
setting transpose −3 and noting the capo yourself. Until then the screen looks
identical; only the app's notion of the sounding key differs.

### Layout

Two modes, because they solve different problems:

- **Flowing** (default) — chords sit above the syllable they belong to and reflow
  to any width. This is what makes a phone usable.
- **Monospace** — preserves the original column alignment exactly. Horizontal
  scroll on narrow screens. For when a sheet's spacing is load-bearing.

Font size is a **zoom control** (`A⁻ A⁺`, plus pinch on touch).

### What is persisted, and where

Split by what the state is actually *about*:

| State | Lives in | Synced? |
|---|---|---|
| transpose, capo | `song.prefs` | **yes** — a property of the song |
| font size, layout mode | device `localStorage` | **no** — a property of the screen |

Syncing font size from a phone to a laptop would be actively wrong: you want big
text on the phone and small on the laptop. Keeping device state out of the synced
row also means it needs no conflict story at all. Neither ever goes inside the
ChordPro body.

### Lock and edit

The sheet is **locked by default** — a padlock in the header. Locked is the
playing state: nothing is editable, so nothing gets nudged by a stray tap while
your hands are on the guitar.

Unlocking reveals the **raw ChordPro source in a textarea**, in the song's stored
key. Edit chords, move them along the lyric, add or delete them, restructure
sections — it is all just text, so all of it works with no bespoke editing UI.
Re-lock to parse and save.

Showing the *stored* text rather than the transposed view is what makes this
safe. The obvious alternative — tap a chord in the rendered sheet and retype it —
has a trap: if the view is transposed to G and you write the edited chord
straight back, you have silently re-keyed the song and broken the single-source-
of-truth rule. Editing raw source in the original key makes that
unrepresentable. If inline editing is added later, the rule it must follow is:
**shift the edit by `−transpose` before writing.**

### Diagrams

Chord diagrams are rendered as SVG from a bundled fingering dataset (~200 KB
covering guitar; ukulele and piano are a later, additive change since the
renderer takes a generic fingering shape). Tapping a chord in the sheet opens
alternate voicings. Diagrams follow the **displayed** chord.

Candidate datasets (licence unverified — settle before bundling):
[tombatossals/chords-db](https://github.com/tombatossals/chords-db) (leading —
also covers ukulele),
[szaza/guitar-chords-db-json](https://github.com/szaza/guitar-chords-db-json)
(99k chords, likely more than needed), and ChordPro's own bundled definitions.

---

## 6. Sync

Offline-first. **The local IndexedDB copy is the one you play from — always.**

Offline-first here means the *library and player* never wait on the network, not
that the app pretends the network doesn't exist. In practice there is usually
wifi, and two features are allowed to depend on it:

| Path | Needs network? |
|---|---|
| browse, open, play, transpose, edit, delete | **never** — straight to IndexedDB |
| auto-save | no — writes land locally and sync in the background |
| sync | yes, best-effort. Failure is a status indicator, never a blocked action |
| search / import (Phase 3) | yes, inherently — it queries other sites |

The rule that keeps this honest: **a local write always succeeds.** Auto-save
commits to IndexedDB and marks the row dirty; pushing it upstream is a separate,
retryable concern. Nothing in the playing path ever shows a spinner.

```
  device A                    server                    device B
 ┌────────┐   push dirty    ┌────────┐   pull since   ┌────────┐
 │IndexedDB│ ──────────────▶│Postgres│ ◀──────────────│IndexedDB│
 └────────┘   pull since    └────────┘   push dirty   └────────┘
```

- Every row carries `updated_at` and a local `dirty` flag.
- Sync = push everything dirty, then pull everything changed since the last
  successful sync timestamp.
- **Conflicts resolve last-write-wins on `updated_at`.** This is a deliberate
  choice, not an oversight: for one person editing their own songbook, real
  conflicts are vanishingly rare, and CRDTs would be an enormous amount of
  machinery for a problem you don't have.
- **Deletes are soft** (`deleted_at` tombstone). A hard delete is invisible to
  the other device, which would resurrect the song on next sync — a bug that is
  extremely annoying and extremely easy to avoid up front.

### Schema

```sql
song (
  id          UUID PRIMARY KEY,
  owner_id    UUID NOT NULL,          -- single user for now, see below
  title       TEXT NOT NULL,
  artist      TEXT,
  chordpro    TEXT NOT NULL,          -- the source of truth
  source_url  TEXT, source TEXT,      -- provenance: where it came from
  prefs       JSONB,                  -- key, capo, font size, layout
  created_at  TIMESTAMPTZ, updated_at TIMESTAMPTZ, deleted_at TIMESTAMPTZ
)
setlist       (id, owner_id, name, …timestamps)
setlist_song  (setlist_id, song_id, position)
```

### Multi-account is a planned direction

Not "someday, maybe" — the intent is that other people eventually get an account
on the same server, each with their own songs. That does **not** mean building
accounts now. It means the two things that would otherwise force a rewrite are
in place from the first commit:

1. **`owner_id` on every user-owned row**, populated with a single constant for
   now. Every query already filters by it, so nothing changes shape later.
2. **Exactly one auth seam.** Every endpoint resolves ownership through a single
   `current_owner(request) -> owner_id`. Today it compares one bearer token from
   an env var and returns the constant. Later it looks up a real user. That is
   one function replaced, not a migration touching every query.

What is deliberately *not* built yet: a `user` table, registration, sessions,
password reset. They add no structure that (1) and (2) don't already provide,
and dead tables are the kind of weight this project is trying to avoid.

One consequence worth recording now: the moment there is more than one account,
`/api/proxy` and the search endpoints must sit **behind the same auth seam** as
the songs. An unauthenticated proxy shared with other users is someone else's
SSRF, not just your own.

---

## 7. Build order

Each phase ends somewhere you'd genuinely want to stop.

| | Phase | Ends with |
|---|---|---|
| **0** | Scaffold | SvelteKit + FastAPI skeletons, vitest, schema, fly.toml |
| **1** | Music core + ChordPro + text parser | Pure logic, fully unit-tested. No UI yet. |
| **2** | Library + player | **Genuinely useful.** Paste a song, play it, transpose it, edit it, see diagrams — all offline, no server. |
| **3** | Import | Search and one-tap import from UG + Boîte à Chansons. |
| **4** | Sync + deploy | Live on Fly, installed on your phone, library shared across devices. |
| **5** | Later | Autoscroll, setlists, ukulele/piano, PDF export, real accounts. |

The order is chosen so the risky, breakable part (scraping) lands *after* the app
already works. If UG changes their markup during Phase 3, you still have a
working app — you just paste songs in while you fix the adapter.

**The chord-over-lyric text parser sits in Phase 1, with the music core**, not
with the import UI it feeds. §4 calls it the foundation rather than a fallback,
and it has exactly the profile of everything else in Phase 1: pure, no I/O, and
full of edge cases that want fixtures. Grouping it there also leaves Phase 2 as
purely UI and storage, which is a cleaner seam than splitting the parsers across
two phases.

**Key detection (`music/key.ts`) sits in Phase 2**, not Phase 1, because nothing
consumes it until the player needs a default key to show. It is pure logic and
would be comfortable in Phase 1, but writing it there would be building ahead of
need.

**Autoscroll deferred to Phase 5** since you didn't flag it for v1, but it's
genuinely cheap once the player exists (a `requestAnimationFrame` loop plus the
Screen Wake Lock API to stop the phone sleeping mid-song) — easy to pull forward
into Phase 2 if you want it sooner.
