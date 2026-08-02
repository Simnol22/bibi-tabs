<script lang="ts">
	import type { Line, Part } from '$lib/chordpro/parse';
	import { transpose } from '$lib/music/transpose';
	import type { Layout } from '$lib/stores/device.svelte';

	interface Props {
		lines: Line[];
		semitones: number;
		displayKey: string;
		layout: Layout;
		fontSize: number;
		onChord: (chord: string) => void;
	}

	let { lines, semitones, displayKey, layout, fontSize, onChord }: Props = $props();

	const shown = (chord: string): string => transpose(chord, semitones, displayKey);

	/** Directives the header already shows, so the sheet stays quiet. */
	const HIDDEN = ['title', 'artist', 'key', 'capo', 'soc', 'eoc', 'sov', 'eov'];

	/**
	 * One inline-block per word rather than per chord run, so a long lyric wraps
	 * on a phone instead of overflowing. Only the first word of a run carries
	 * the chord.
	 */
	function words(parts: Part[]): Part[] {
		const out: Part[] = [];
		for (const part of parts) {
			const chunks = part.text === '' ? [''] : (part.text.match(/\S+\s*|\s+/g) ?? ['']);
			chunks.forEach((text, i) => out.push({ chord: i === 0 ? part.chord : null, text }));
		}
		return out;
	}

	/**
	 * Rebuild the original two-row layout: chords on their own line, positioned
	 * at the column where their lyric starts.
	 */
	function columns(parts: Part[]): { chords: string; lyric: string } {
		let chords = '';
		let lyric = '';
		for (const part of parts) {
			if (part.chord !== null) {
				if (chords.length > lyric.length) chords += ' ';
				chords = chords.padEnd(lyric.length) + shown(part.chord);
			}
			lyric += part.text;
		}
		return { chords, lyric };
	}
</script>

<div class="sheet" style="font-size: {fontSize}px">
	{#each lines as line, i (i)}
		{#if line.type === 'empty'}
			<div class="gap"></div>
		{:else if line.type === 'directive'}
			{#if !HIDDEN.includes(line.name)}
				<div class="section">{line.value || line.name}</div>
			{/if}
		{:else if line.type === 'lyric'}
			{#if layout === 'monospace'}
				{@const row = columns(line.parts)}
				<pre class="mono">{#if row.chords}<span class="chord">{row.chords}</span>{'\n'}{/if}{row.lyric}</pre>
			{:else}
				<div class="row">
					{#each words(line.parts) as unit, j (j)}
						<span class="unit">
							{#if unit.chord}
								{@const chord = shown(unit.chord)}
								<button class="chord tap" onclick={() => onChord(chord)}>{chord}</button>
							{:else}
								<span class="chord"></span>
							{/if}
							<span class="text">{unit.text}</span>
						</span>
					{/each}
				</div>
			{/if}
		{/if}
	{/each}
</div>

<style>
	.sheet {
		padding: 0.5rem 0 4rem;
	}

	.row {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
	}

	.unit {
		display: inline-flex;
		flex-direction: column;
	}

	.chord {
		color: var(--accent);
		font-weight: 600;
		line-height: 1.35;
		white-space: pre;
		min-height: 1.35em;
	}

	/* A chord is a tap target, but must not look or space like a button. */
	.tap {
		all: unset;
		color: var(--accent);
		font-weight: 600;
		cursor: pointer;
		white-space: pre;
	}

	.tap:hover {
		text-decoration: underline;
	}

	.text {
		white-space: pre;
	}

	.gap {
		height: 1em;
	}

	.section {
		color: var(--muted);
		font-weight: 600;
		font-size: 0.85em;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		margin: 1.1em 0 0.3em;
	}

	/* Monospace mode keeps the sheet's original column alignment, so it scrolls
	   sideways rather than reflowing. */
	.mono {
		font-family: ui-monospace, 'SF Mono', Menlo, monospace;
		margin: 0;
		line-height: 1.35;
		white-space: pre;
	}

	.sheet:has(.mono) {
		overflow-x: auto;
	}
</style>
