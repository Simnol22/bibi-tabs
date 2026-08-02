<script lang="ts">
	import { goto } from '$app/navigation';
	import { createSong } from '$lib/db/songs';
	import { textToChordPro } from '$lib/import/text';

	let title = $state('');
	let artist = $state('');
	let pasted = $state('');
	/** Set once converted, then freely editable -- this is the review step. */
	let chordpro = $state<string | null>(null);
	let saving = $state(false);

	/** Text that already has inline [C] chords is ChordPro; don't run it twice. */
	const isChordPro = (text: string): boolean => /\[[A-G][#b]?[^\]]*\]/.test(text);

	function convert() {
		chordpro = isChordPro(pasted) ? pasted : textToChordPro(pasted);
	}

	async function save() {
		if (chordpro === null) return;
		saving = true;
		const song = await createSong({
			title: title.trim() || 'Untitled',
			artist: artist.trim(),
			chordpro,
			source: 'paste'
		});
		await goto(`/song/${song.id}`);
	}
</script>

<header>
	<a href="/">← Library</a>
	<h1>Add a song</h1>
</header>

<div class="fields">
	<label>
		<span>Title</span>
		<input bind:value={title} placeholder="Yesterday" />
	</label>
	<label>
		<span>Artist</span>
		<input bind:value={artist} placeholder="The Beatles" />
	</label>
</div>

{#if chordpro === null}
	<label class="block">
		<span>Paste the song</span>
		<textarea
			bind:value={pasted}
			rows="14"
			placeholder={'C          G\nYesterday, all my troubles…\n\nChords above lyrics, or ChordPro — either works.'}
		></textarea>
	</label>
	<div class="actions">
		<button onclick={convert} disabled={pasted.trim() === ''}>Convert →</button>
	</div>
{:else}
	<label class="block">
		<span>Check it over</span>
		<textarea bind:value={chordpro} rows="14" spellcheck="false" class="mono"></textarea>
	</label>
	<p class="hint">
		Chords are in square brackets now. Fix anything the parser misread before saving — this text is
		what gets stored, in this key.
	</p>
	<div class="actions">
		<button onclick={() => (chordpro = null)}>← Back</button>
		<button class="primary" onclick={save} disabled={saving}>Save to library</button>
	</div>
{/if}

<style>
	header {
		display: flex;
		align-items: baseline;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	header a {
		text-decoration: none;
		font-size: 0.9rem;
	}

	.fields {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}

	.fields label {
		flex: 1;
		min-width: 12rem;
	}

	label {
		display: block;
	}

	label span {
		display: block;
		color: var(--muted);
		font-size: 0.85rem;
		margin-bottom: 0.25rem;
	}

	.block {
		margin-bottom: 0.75rem;
	}

	textarea {
		font-family: ui-monospace, 'SF Mono', Menlo, monospace;
		font-size: 0.9rem;
		line-height: 1.45;
		resize: vertical;
		white-space: pre;
		overflow-wrap: normal;
		overflow-x: auto;
	}

	.hint {
		color: var(--muted);
		font-size: 0.85rem;
		margin: 0 0 1rem;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		justify-content: flex-end;
	}

	.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}
</style>
