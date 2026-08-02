/**
 * The local library. This is the copy the app plays from -- always.
 *
 * Mirrors server/schema.sql, minus owner_id: the server assigns that from the
 * authenticated request, so a client-side copy would be dead weight.
 *
 * There is no `dirty` flag either. "What needs pushing" is derivable as
 * `updated_at > lastSyncedAt`, so Phase 4 can add sync without a column that
 * every write would otherwise have to remember to maintain.
 */

import Dexie, { type Table } from 'dexie';

export interface SongPrefs {
	/** Semitones from the stored key. The only pitch transform. */
	transpose: number;
	/** An annotation printed at the top of the sheet. Moves nothing. */
	capo: number;
}

export interface Song {
	id: string;
	title: string;
	artist: string;
	/** The single source of truth, in the original key. */
	chordpro: string;
	source: string;
	source_url: string | null;
	prefs: SongPrefs;
	created_at: string;
	updated_at: string;
	/** Tombstone. A hard delete would resurrect on the other device's sync. */
	deleted_at: string | null;
}

class Library extends Dexie {
	songs!: Table<Song, string>;

	constructor() {
		super('bibi-tabs');
		// deleted_at is not indexed: IndexedDB drops nulls from indexes, so
		// live rows would fall out of it. Filtering in JS is fine at this size.
		this.version(1).stores({ songs: 'id, updated_at' });
	}
}

export const db = new Library();
