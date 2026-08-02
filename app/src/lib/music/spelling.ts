/**
 * Note names, pitch classes, and the choice between F# and Gb.
 *
 * Spelling is derived from the target key's position on the circle of fifths --
 * sharp keys get sharps, flat keys get flats -- rather than from a fixed table.
 * A fixed table is what makes transposed sheets in other apps read wrong.
 */

const SHARP_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

/** The practical keys, ordered by signature: index 0 is 7 flats, index 14 is 7 sharps. */
const MAJOR_KEYS = ['Cb', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F', 'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#'];
const MINOR_KEYS = ['Abm', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm', 'Dm', 'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m', 'A#m'];

const LETTER_PITCH: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

const mod12 = (n: number): number => ((n % 12) + 12) % 12;

/** Imported sheets are full of ♯ and ♭; everything downstream expects # and b. */
export function normalizeAccidentals(text: string): string {
	return text.replace(/♯/g, '#').replace(/♭/g, 'b');
}

/** Drop the minor marker to get the key's tonic note name. */
export function tonic(key: string): string {
	const k = normalizeAccidentals(key.trim());
	return k.endsWith('m') ? k.slice(0, -1) : k;
}

/** The practical major or minor keys, ordered flattest to sharpest. */
export function keyNames(minor: boolean): readonly string[] {
	return minor ? MINOR_KEYS : MAJOR_KEYS;
}

export function pitchClass(note: string): number {
	const n = normalizeAccidentals(note.trim());
	const base = LETTER_PITCH[n.slice(0, 1).toUpperCase()];
	if (base === undefined) throw new Error(`Not a note name: ${note}`);

	let pitch = base;
	for (const char of n.slice(1)) {
		if (char === '#') pitch += 1;
		else if (char === 'b') pitch -= 1;
		else throw new Error(`Not a note name: ${note}`);
	}
	return mod12(pitch);
}

/** Sharps count positive, flats negative. C major and A minor are 0. */
export function keySignature(key: string): number {
	const k = normalizeAccidentals(key.trim());
	const index = keyNames(k.endsWith('m')).indexOf(k);
	if (index === -1) throw new Error(`Unknown key: ${key}`);
	return index - 7;
}

/**
 * Name a pitch as the target key would write it.
 *
 * Limited to the twelve practical names: pitch 11 in Gb major comes back as B,
 * not the theoretically correct Cb. Chasing Cb and E# needs a per-key diatonic
 * speller and puts chords on the page that no guitarist wants to read.
 */
export function spell(pitch: number, key: string): string {
	const names = keySignature(key) < 0 ? FLAT_NAMES : SHARP_NAMES;
	return names[mod12(pitch)];
}
