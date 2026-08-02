<script lang="ts">
	import { page } from '$app/state';
	import ChordDiagram from '$lib/components/ChordDiagram.svelte';
	import ChordSheet from '$lib/components/ChordSheet.svelte';
	import Transposer from '$lib/components/Transposer.svelte';
	import { parse, type Line } from '$lib/chordpro/parse';
	import type { Song } from '$lib/db/schema';
	import { getSong, updateSong } from '$lib/db/songs';
	import { fingerings } from '$lib/fingering/guitar';
	import { detectKey } from '$lib/music/key';
	import { keySignature } from '$lib/music/spelling';
	import { transposeKey } from '$lib/music/transpose';
	import { device, setLayout, zoom } from '$lib/stores/device.svelte';

	const AUTOSAVE_MS = 600;

	let song = $state<Song | null>(null);
	let missing = $state(false);
	/** Locked is the playing state: nothing moves under a stray tap. */
	let locked = $state(true);
	let draft = $state('');
	let tapped = $state<string | null>(null);
	let saveTimer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		const id = page.params.id;
		if (!id) return;
		getSong(id).then((found) => {
			if (found && found.deleted_at === null) {
				song = found;
				draft = found.chordpro;
			} else {
				missing = true;
			}
		});
	});

	let lines = $derived(song ? parse(song.chordpro) : []);

	let chordTokens = $derived(
		lines.flatMap((line) =>
			line.type === 'lyric' ? line.parts.flatMap((p) => (p.chord ? [p.chord] : [])) : []
		)
	);

	/** A {key} directive wins if it names a key we understand; else we guess. */
	let storedKey = $derived.by(() => {
		const declared = directive(lines, 'key');
		if (declared) {
			try {
				keySignature(declared);
				return declared;
			} catch {
				/* not a key name we know -- fall through to detection */
			}
		}
		return detectKey(chordTokens) ?? 'C';
	});

	let transposeBy = $derived(song?.prefs.transpose ?? 0);
	let capo = $derived(song?.prefs.capo ?? 0);
	let displayKey = $derived(transposeKey(storedKey, transposeBy));
	let voicings = $derived(tapped ? fingerings(tapped) : []);

	function directive(all: Line[], name: string): string | null {
		for (const line of all) {
			if (line.type === 'directive' && line.name === name && line.value) return line.value;
		}
		return null;
	}

	async function savePrefs(patch: { transpose?: number; capo?: number }) {
		if (!song) return;
		song = { ...song, prefs: { ...song.prefs, ...patch } };
		await updateSong(song.id, { prefs: patch });
	}

	/** Local write, straight to IndexedDB. Never waits on anything. */
	async function commit() {
		if (!song || draft === song.chordpro) return;
		await updateSong(song.id, { chordpro: draft });
		song = { ...song, chordpro: draft };
	}

	function onEdit() {
		clearTimeout(saveTimer);
		saveTimer = setTimeout(commit, AUTOSAVE_MS);
	}

	function toggleLock() {
		if (locked) {
			draft = song?.chordpro ?? '';
		} else {
			clearTimeout(saveTimer);
			commit();
		}
		locked = !locked;
	}
</script>

{#if missing}
	<p><a href="/">← Library</a></p>
	<p class="muted">That song isn't here. It may have been deleted.</p>
{:else if song}
	<header>
		<a class="back" href="/">←</a>
		<div class="titles">
			<h1>{song.title}</h1>
			{#if song.artist}<span class="muted">{song.artist}</span>{/if}
		</div>
		<button class:active={!locked} onclick={toggleLock} title={locked ? 'Unlock to edit' : 'Done'}>
			{locked ? '🔒' : '🔓'}
		</button>
	</header>

	<div class="controls">
		<Transposer
			{displayKey}
			{transposeBy}
			{capo}
			onTranspose={(semitones) => savePrefs({ transpose: semitones })}
			onCapo={(fret) => savePrefs({ capo: fret })}
		/>
		<div class="spacer"></div>
		<div class="group">
			<button onclick={() => zoom(-2)} aria-label="Smaller text">A−</button>
			<button onclick={() => zoom(2)} aria-label="Larger text">A+</button>
			<button
				onclick={() => setLayout(device.layout === 'flowing' ? 'monospace' : 'flowing')}
				title="Switch layout"
			>
				{device.layout === 'flowing' ? 'Flowing' : 'Columns'}
			</button>
		</div>
	</div>

	{#if capo > 0}
		<p class="capo">Capo {capo}</p>
	{/if}

	{#if locked}
		<ChordSheet
			{lines}
			semitones={transposeBy}
			{displayKey}
			layout={device.layout}
			fontSize={device.fontSize}
			onChord={(chord) => (tapped = chord)}
		/>
	{:else}
		<p class="hint">
			Editing the stored song, in its own key{transposeBy !== 0
				? ` — not the ${displayKey} you were viewing`
				: ''}. Saves as you type.
		</p>
		<textarea bind:value={draft} oninput={onEdit} spellcheck="false" rows="24"></textarea>
	{/if}

	{#if tapped}
		<aside class="diagrams">
			<div class="diagrams-head">
				<strong>{tapped}</strong>
				<button onclick={() => (tapped = null)} aria-label="Close">×</button>
			</div>
			{#if voicings.length === 0}
				<p class="muted">No shape for this one yet.</p>
			{:else}
				<div class="voicings">
					{#each voicings as fingering, i (i)}
						<ChordDiagram {fingering} />
					{/each}
				</div>
			{/if}
		</aside>
	{/if}
{/if}

<style>
	header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.back {
		text-decoration: none;
		font-size: 1.2rem;
	}

	.titles {
		flex: 1;
		min-width: 0;
	}

	h1 {
		font-size: 1.25rem;
	}

	.muted {
		color: var(--muted);
		font-size: 0.9rem;
	}

	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		align-items: center;
		padding: 0.6rem 0;
		border-top: 1px solid var(--border);
		border-bottom: 1px solid var(--border);
		position: sticky;
		top: 0;
		background: var(--bg);
		z-index: 2;
	}

	.spacer {
		flex: 1;
	}

	.group {
		display: flex;
		gap: 0.35rem;
	}

	.active {
		border-color: var(--accent);
		color: var(--accent);
	}

	.capo {
		margin: 0.9rem 0 0;
		font-weight: 600;
		color: var(--accent);
	}

	.hint {
		color: var(--muted);
		font-size: 0.85rem;
		margin: 1rem 0 0.5rem;
	}

	textarea {
		font-family: ui-monospace, 'SF Mono', Menlo, monospace;
		font-size: 0.9rem;
		line-height: 1.45;
		white-space: pre;
		overflow-wrap: normal;
		overflow-x: auto;
		resize: vertical;
	}

	.diagrams {
		position: sticky;
		bottom: 0;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem;
		margin-top: 1rem;
		box-shadow: 0 -6px 24px rgb(0 0 0 / 0.12);
	}

	.diagrams-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.diagrams-head button {
		border: none;
		background: none;
		font-size: 1.3rem;
		line-height: 1;
		padding: 0 0.3rem;
	}

	.voicings {
		display: flex;
		gap: 1.25rem;
		overflow-x: auto;
		padding-bottom: 0.25rem;
	}
</style>
