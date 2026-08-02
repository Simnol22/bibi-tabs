/**
 * Guess a song's key from the chords it uses.
 *
 * Only ever a default: it seeds the player's key selector, and the reading the
 * player shows is whatever the user last chose. Nothing here is persisted.
 */

import { parseChord, type Chord } from './chord';
import { pitchClass } from './spelling';
import { transposeKey } from './transpose';

type Triad = 'maj' | 'min' | 'dim' | 'aug';

/** Scale degrees in semitones, and the triad each one naturally carries. */
const MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11];
const MAJOR_TRIADS: Triad[] = ['maj', 'min', 'min', 'maj', 'maj', 'min', 'dim'];
const MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10];
const MINOR_TRIADS: Triad[] = ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj'];

const EXACT = 2;
const IN_SCALE = 1;
const STARTS_ON_TONIC = 1;
const ENDS_ON_TONIC = 1.5;

export function detectKey(tokens: string[]): string | null {
	const chords = tokens.map(parseChord).filter((c): c is Chord => c !== null);
	if (chords.length === 0) return null;

	let best = '';
	let bestScore = -Infinity;

	for (let tonic = 0; tonic < 12; tonic++) {
		for (const minor of [false, true]) {
			const score = scoreKey(chords, tonic, minor);
			if (score > bestScore) {
				bestScore = score;
				best = nameKey(tonic, minor);
			}
		}
	}
	return best;
}

/**
 * Name the key on `tonic`, reusing the transposer's "fewest accidentals" rule
 * so a detected key is one that spell() and transposeKey() both accept.
 */
function nameKey(tonic: number, minor: boolean): string {
	const seed = minor ? 'Am' : 'C';
	return transposeKey(seed, tonic - pitchClass(seed === 'Am' ? 'A' : 'C'));
}

function scoreKey(chords: Chord[], tonic: number, minor: boolean): number {
	const scale = minor ? MINOR_SCALE : MAJOR_SCALE;
	const triads = minor ? MINOR_TRIADS : MAJOR_TRIADS;

	let score = 0;
	for (const chord of chords) {
		const degree = scale.indexOf((pitchClass(chord.root) - tonic + 12) % 12);
		if (degree === -1) continue;

		const actual = triad(chord);
		// The V of a minor key is major far more often than not -- harmonic
		// minor is the default in practice, not an exception.
		const expected = minor && degree === 4 && actual === 'maj' ? 'maj' : triads[degree];
		score += actual === expected ? EXACT : IN_SCALE;
	}

	const first = pitchClass(chords[0].root);
	const last = pitchClass(chords[chords.length - 1].root);
	if (first === tonic) score += STARTS_ON_TONIC;
	if (last === tonic) score += ENDS_ON_TONIC;
	return score;
}

function triad(chord: Chord): Triad {
	switch (chord.quality) {
		case 'm':
		case 'min':
		case '-':
			// mMaj7 and m7b5 are still minor-rooted for this purpose.
			return 'min';
		case 'dim':
		case '°':
		case 'ø':
			return 'dim';
		case 'aug':
		case '+':
			return 'aug';
		default:
			return 'maj';
	}
}
