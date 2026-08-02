<script lang="ts">
	interface Props {
		displayKey: string;
		transposeBy: number;
		capo: number;
		onTranspose: (semitones: number) => void;
		onCapo: (fret: number) => void;
	}

	let { displayKey, transposeBy, capo, onTranspose, onCapo }: Props = $props();
</script>

<div class="transposer">
	<div class="group">
		<span class="label">Key</span>
		<button onclick={() => onTranspose(transposeBy - 1)} aria-label="Down a semitone">−</button>
		<strong class="value">{displayKey}</strong>
		<button onclick={() => onTranspose(transposeBy + 1)} aria-label="Up a semitone">+</button>
		{#if transposeBy !== 0}
			<button class="reset" onclick={() => onTranspose(0)} title="Back to the stored key">
				{transposeBy > 0 ? `+${transposeBy}` : transposeBy}
			</button>
		{/if}
	</div>

	<!-- Capo is an annotation: it is recorded and printed, and moves nothing. -->
	<label class="group">
		<span class="label">Capo</span>
		<select value={capo} onchange={(e) => onCapo(Number(e.currentTarget.value))}>
			{#each Array(12) as _, fret (fret)}
				<option value={fret}>{fret === 0 ? 'none' : fret}</option>
			{/each}
		</select>
	</label>
</div>

<style>
	.transposer {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		align-items: center;
	}

	.group {
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.label {
		color: var(--muted);
		font-size: 0.85rem;
	}

	.value {
		min-width: 2.4em;
		text-align: center;
	}

	.reset {
		font-size: 0.8rem;
		padding: 0.15rem 0.4rem;
		color: var(--muted);
	}

	select {
		font: inherit;
		color: inherit;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.35rem 0.4rem;
	}
</style>
