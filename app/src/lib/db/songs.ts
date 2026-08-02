/**
 * Library reads and writes. Every one of these is local and synchronous with
 * respect to the network -- a write never waits on a server, and never fails
 * because there isn't one.
 */

import { db, type Song, type SongPrefs } from './schema';

const now = (): string => new Date().toISOString();

export async function listSongs(): Promise<Song[]> {
	const all = await db.songs.orderBy('updated_at').reverse().toArray();
	return all.filter((song) => song.deleted_at === null);
}

export function getSong(id: string): Promise<Song | undefined> {
	return db.songs.get(id);
}

export async function createSong(
	fields: Pick<Song, 'title' | 'artist' | 'chordpro' | 'source'> & { source_url?: string | null }
): Promise<Song> {
	const timestamp = now();
	const song: Song = {
		id: crypto.randomUUID(),
		source_url: fields.source_url ?? null,
		prefs: { transpose: 0, capo: 0 },
		created_at: timestamp,
		updated_at: timestamp,
		deleted_at: null,
		...fields
	};
	await db.songs.add(song);
	return song;
}

export async function updateSong(
	id: string,
	patch: Partial<Pick<Song, 'title' | 'artist' | 'chordpro'>> & { prefs?: Partial<SongPrefs> }
): Promise<void> {
	const song = await db.songs.get(id);
	if (!song) return;

	await db.songs.put({
		...song,
		...patch,
		prefs: { ...song.prefs, ...patch.prefs },
		updated_at: now()
	});
}

/** Soft, always. See invariant 5. */
export async function deleteSong(id: string): Promise<void> {
	const timestamp = now();
	await db.songs.update(id, { deleted_at: timestamp, updated_at: timestamp });
}

export function searchSongs(songs: Song[], query: string): Song[] {
	const needle = query.trim().toLowerCase();
	if (needle === '') return songs;
	return songs.filter((song) =>
		`${song.title} ${song.artist} ${song.chordpro}`.toLowerCase().includes(needle)
	);
}
