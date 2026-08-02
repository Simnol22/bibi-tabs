/**
 * Shifting chords and keys.
 *
 * `displayed = stored + transpose`, always computed at render time. Nothing here
 * writes anywhere; the stored ChordPro keeps its original key forever.
 *
 * There is no capo function. Capo is an annotation printed at the top of the
 * sheet, not a transform -- see ARCHITECTURE.md §5.
 */

import { formatChord, parseChord } from './chord';
import { keyNames, keySignature, normalizeAccidentals, pitchClass, spell, tonic } from './spelling';

/**
 * Shift one chord symbol, spelling the result for `targetKey`.
 *
 * A token that is not a chord comes back untouched. Sheets are full of `N.C.`,
 * repeat marks and section labels, and mangling them is worse than ignoring them.
 */
export function transpose(token: string, semitones: number, targetKey: string): string {
	const chord = parseChord(token);
	if (!chord) return token;

	const shift = (note: string): string => spell(pitchClass(note) + semitones, targetKey);

	return formatChord({
		...chord,
		root: shift(chord.root),
		bass: chord.bass === null ? null : shift(chord.bass)
	});
}

/**
 * Shift a key name, picking the most readable spelling of the destination.
 *
 * Fewest accidentals wins: up a semitone from A is Bb (2 flats), never A#
 * (which would need ten sharps). Where the two spellings tie at six, keep
 * heading the way the source key was already going -- F is flat, so F+1 is Gb.
 */
export function transposeKey(key: string, semitones: number): string {
	const minor = normalizeAccidentals(key.trim()).endsWith('m');
	const sourceSignature = keySignature(key);
	const target = pitchClass(tonic(key)) + semitones;

	const candidates = keyNames(minor).filter((k) => pitchClass(tonic(k)) === ((target % 12) + 12) % 12);
	if (candidates.length === 0) throw new Error(`No key a ${semitones}-semitone shift from ${key}`);

	return candidates.reduce((best, candidate) => {
		const a = Math.abs(keySignature(candidate));
		const b = Math.abs(keySignature(best));
		if (a !== b) return a < b ? candidate : best;
		// Tied on accidentals: match the direction the source key leaned.
		const wantsFlats = sourceSignature < 0;
		return keySignature(candidate) < 0 === wantsFlats ? candidate : best;
	});
}
