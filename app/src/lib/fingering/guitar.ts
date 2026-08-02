/**
 * Chord symbol -> guitar fingerings.
 *
 * Data is chords-db (MIT, (c) 2016 David Rubert), flattened to "key|suffix" and
 * stripped of its midi arrays -- see LICENSE-chords-db. Bundled rather than
 * fetched so tapping a chord works with no signal.
 *
 * This lives outside lib/music/ deliberately: music/ is pure theory with no
 * data files, and this is a lookup table.
 */

import { parseChord, type Chord } from '../music/chord';
import { pitchClass } from '../music/spelling';
import data from './guitar.json';

export interface Fingering {
	/** Six strings, low E first. -1 is muted, 0 is open, else a fret offset from baseFret. */
	frets: number[];
	/** 0 for none, otherwise 1-4. */
	fingers: number[];
	baseFret: number;
	barres?: number[];
	/** The barre is better drawn as a capo bar. */
	capo?: boolean;
}

const DB = data as Record<string, Fingering[]>;

/** The twelve root spellings the dataset indexes on. */
const ROOTS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'];
/** Slash basses are indexed under both spellings, so try the other one too. */
const ALT_ROOTS: Record<string, string> = {
	'C#': 'Db',
	Eb: 'D#',
	'F#': 'Gb',
	Ab: 'G#',
	Bb: 'A#'
};

const QUALITY: Record<string, string> = {
	'': '',
	m: 'm',
	min: 'm',
	'-': 'm',
	maj: 'maj',
	M: 'maj',
	dim: 'dim',
	'°': 'dim',
	aug: 'aug',
	'+': 'aug'
};

/** Spellings the parser produces that the dataset files differently. */
const ALIAS: Record<string, string> = {
	'm7-5': 'm7b5',
	'7-5': '7b5',
	'7#5': 'aug7',
	'7+5': 'aug7',
	'9#5': 'aug9'
};

export function fingerings(token: string): Fingering[] {
	const chord = parseChord(token);
	if (!chord) return [];

	const root = ROOTS[pitchClass(chord.root)];
	const core = coreSuffix(chord);

	for (const suffix of suffixCandidates(core, chord.bass)) {
		const found = DB[`${root}|${suffix}`];
		if (found) return found;
	}
	return [];
}

/** The chord minus its root and bass: '' for major, 'm7', 'sus4', 'maj7'… */
function coreSuffix(chord: Chord): string {
	// Half-diminished is filed as m7b5, and its '7' is already implied.
	if (chord.quality === 'ø') return 'm7b5';
	const core = (QUALITY[chord.quality] ?? chord.quality) + chord.ext;
	return ALIAS[core] ?? core;
}

/**
 * Most specific first. A slash chord the dataset lacks falls back to the base
 * shape, which is more use than an empty box.
 */
function suffixCandidates(core: string, bass: string | null): string[] {
	const plain = core === '' ? 'major' : core === 'm' ? 'minor' : core;
	if (bass === null) return [plain];

	const bassName = ROOTS[pitchClass(bass)];
	const alt = ALT_ROOTS[bassName];
	return [
		`${core}/${bassName}`,
		...(alt ? [`${core}/${alt}`] : []),
		plain
	];
}
