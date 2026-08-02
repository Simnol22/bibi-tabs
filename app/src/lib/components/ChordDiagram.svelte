<script lang="ts">
	import type { Fingering } from '$lib/fingering/guitar';

	interface Props {
		fingering: Fingering;
		/** Rendered width in px; the SVG scales to it. */
		width?: number;
	}

	let { fingering, width = 104 }: Props = $props();

	const PAD = 14;
	const STRING_GAP = 15;
	const FRET_GAP = 19;
	const TOP = 20; // room for the open/muted markers above the nut

	const strings = 6;
	const w = PAD * 2 + STRING_GAP * (strings - 1);

	// Most shapes fit four frets; a stretched one gets an extra space rather
	// than being cropped.
	let fretCount = $derived(Math.max(4, ...fingering.frets));
	let h = $derived(TOP + FRET_GAP * fretCount + 6);

	const x = (stringIndex: number): number => PAD + stringIndex * STRING_GAP;
	const y = (fret: number): number => TOP + (fret - 0.5) * FRET_GAP;

	/** A barre runs between the outermost strings stopped at that fret. */
	function barreSpan(fret: number): { from: number; to: number } {
		const held = fingering.frets.flatMap((f, i) => (f === fret ? [i] : []));
		return { from: Math.min(...held), to: Math.max(...held) };
	}
</script>

<svg viewBox="0 0 {w} {h}" style="width: {width}px" role="img">
	<!-- nut: heavy only when the diagram starts at the top of the neck -->
	<line
		x1={PAD - 1}
		y1={TOP}
		x2={w - PAD + 1}
		y2={TOP}
		stroke="currentColor"
		stroke-width={fingering.baseFret === 1 ? 4 : 1.2}
	/>

	{#each Array(fretCount) as _, f (f)}
		<line
			x1={PAD}
			y1={TOP + (f + 1) * FRET_GAP}
			x2={w - PAD}
			y2={TOP + (f + 1) * FRET_GAP}
			stroke="currentColor"
			stroke-width="1.2"
			opacity="0.5"
		/>
	{/each}

	{#each Array(strings) as _, s (s)}
		<line
			x1={x(s)}
			y1={TOP}
			x2={x(s)}
			y2={TOP + fretCount * FRET_GAP}
			stroke="currentColor"
			stroke-width="1.2"
			opacity="0.5"
		/>
	{/each}

	{#if fingering.baseFret > 1}
		<text class="fret-label" x={w - PAD + 5} y={y(1) + 3}>{fingering.baseFret}</text>
	{/if}

	{#each fingering.barres ?? [] as fret (fret)}
		{@const span = barreSpan(fret)}
		<line
			x1={x(span.from)}
			y1={y(fret)}
			x2={x(span.to)}
			y2={y(fret)}
			stroke="currentColor"
			stroke-width="11"
			stroke-linecap="round"
		/>
	{/each}

	{#each fingering.frets as fret, s (s)}
		{#if fret > 0}
			<circle cx={x(s)} cy={y(fret)} r="5.5" fill="currentColor" />
			{#if fingering.fingers[s] > 0}
				<text class="finger" x={x(s)} y={y(fret) + 3}>{fingering.fingers[s]}</text>
			{/if}
		{:else}
			<text class="marker" x={x(s)} y={TOP - 6}>{fret === 0 ? '○' : '×'}</text>
		{/if}
	{/each}
</svg>

<style>
	svg {
		display: block;
		color: var(--text);
		overflow: visible;
	}

	.marker {
		font-size: 11px;
		text-anchor: middle;
		fill: var(--muted);
	}

	.finger {
		font-size: 8px;
		font-weight: 700;
		text-anchor: middle;
		fill: var(--surface);
	}

	.fret-label {
		font-size: 10px;
		fill: var(--muted);
	}
</style>
