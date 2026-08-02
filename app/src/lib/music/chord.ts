/**
 * Chord symbol parsing.
 *
 * Only the root and the bass carry pitch. Quality and extension ride along as
 * opaque text, because transposition never needs to understand them -- and
 * keeping them verbatim means a sheet reads back exactly as it was written.
 *
 * Returning null for anything that is not a chord is load-bearing: the
 * chord-line heuristic in import/text.ts decides what is a chord line by
 * counting how many tokens survive this function.
 */

import { normalizeAccidentals } from './spelling';

export interface Chord {
	root: string;
	/** As written: '', 'm', 'maj', 'dim', '°', '+', … */
	quality: string;
	/** Everything after the quality, verbatim: '7b5', 'sus4', 'add9', … */
	ext: string;
	bass: string | null;
}

const ROOT = '[A-G][#b]?';
const QUALITY = 'maj|min|dim|aug|M|m|°|ø|Δ|\\+|-';
// Single \d rather than \d+ so each position has exactly one matching
// alternative -- a nested quantifier here would backtrack exponentially on a
// long near-miss like 'C1111111111x'.
const EXT_TOKEN = 'sus|add|maj|min|dim|aug|alt|\\d|[#b()+\\-°øΔ]';

const CHORD = new RegExp(`^(${ROOT})(${QUALITY})?((?:${EXT_TOKEN})*)(?:/(${ROOT}))?$`);

export function parseChord(token: string): Chord | null {
	const match = CHORD.exec(normalizeAccidentals(token.trim()));
	if (!match) return null;
	return {
		root: match[1],
		quality: match[2] ?? '',
		ext: match[3] ?? '',
		bass: match[4] ?? null
	};
}

export function formatChord(chord: Chord): string {
	const slash = chord.bass === null ? '' : `/${chord.bass}`;
	return `${chord.root}${chord.quality}${chord.ext}${slash}`;
}
