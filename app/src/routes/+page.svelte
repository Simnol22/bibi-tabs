<script lang="ts">
	import { deleteSong, listSongs, searchSongs } from '$lib/db/songs';
	import type { Song } from '$lib/db/schema';

	let songs = $state<Song[]>([]);
	let query = $state('');
	let loading = $state(true);

	let visible = $derived(searchSongs(songs, query));

	$effect(() => {
		listSongs().then((found) => {
			songs = found;
			loading = false;
		});
	});

	async function remove(song: Song) {
		if (!confirm(`Delete "${song.title}"?`)) return;
		await deleteSong(song.id);
		songs = songs.filter((s) => s.id !== song.id);
	}
</script>

<header>
	<h1>BIBI-tabs</h1>
	<a class="add" href="/import">+ Add song</a>
</header>

{#if songs.length > 0}
	<input bind:value={query} placeholder="Search title, artist or lyrics" aria-label="Search" />
{/if}

{#if loading}
	<p class="muted">Loading…</p>
{:else if songs.length === 0}
	<p class="muted">
		Nothing here yet. <a href="/import">Paste a song</a> to get started — it stays on this device
		and works offline.
	</p>
{:else if visible.length === 0}
	<p class="muted">No song matches “{query}”.</p>
{:else}
	<ul>
		{#each visible as song (song.id)}
			<li>
				<a href="/song/{song.id}">
					<strong>{song.title}</strong>
					{#if song.artist}<span class="muted">{song.artist}</span>{/if}
				</a>
				<button class="remove" onclick={() => remove(song)} aria-label="Delete {song.title}">
					×
				</button>
			</li>
		{/each}
	</ul>
{/if}

<style>
	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.add {
		text-decoration: none;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.4rem 0.7rem;
		white-space: nowrap;
	}

	ul {
		list-style: none;
		padding: 0;
		margin: 1rem 0 0;
	}

	li {
		display: flex;
		align-items: center;
		border-bottom: 1px solid var(--border);
	}

	li a {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		padding: 0.7rem 0.2rem;
		text-decoration: none;
		color: inherit;
	}

	li a:hover strong {
		color: var(--accent);
	}

	.muted {
		color: var(--muted);
		font-size: 0.9rem;
	}

	.remove {
		border: none;
		background: none;
		color: var(--muted);
		font-size: 1.3rem;
		line-height: 1;
		padding: 0.3rem 0.5rem;
	}

	.remove:hover {
		color: var(--danger);
	}
</style>
