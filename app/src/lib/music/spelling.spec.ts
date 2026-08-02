import { describe, it, expect } from 'vitest';
import { pitchClass, keySignature, spell } from './spelling';

describe('pitchClass', () => {
	it('maps naturals', () => {
		expect(['C', 'D', 'E', 'F', 'G', 'A', 'B'].map(pitchClass)).toEqual([0, 2, 4, 5, 7, 9, 11]);
	});

	it('maps sharps and flats to the same pitch', () => {
		expect(pitchClass('F#')).toBe(6);
		expect(pitchClass('Gb')).toBe(6);
	});

	it('accepts unicode accidentals, which imported sheets are full of', () => {
		expect(pitchClass('F♯')).toBe(6);
		expect(pitchClass('B♭')).toBe(10);
	});
});

describe('keySignature', () => {
	it('counts sharps as positive along the circle of fifths', () => {
		expect(keySignature('C')).toBe(0);
		expect(keySignature('G')).toBe(1);
		expect(keySignature('D')).toBe(2);
		expect(keySignature('B')).toBe(5);
		expect(keySignature('C#')).toBe(7);
	});

	it('counts flats as negative', () => {
		expect(keySignature('F')).toBe(-1);
		expect(keySignature('Bb')).toBe(-2);
		expect(keySignature('Db')).toBe(-5);
		expect(keySignature('Cb')).toBe(-7);
	});

	it('gives a minor key the signature of its relative major', () => {
		expect(keySignature('Am')).toBe(0); // relative C
		expect(keySignature('Em')).toBe(1); // relative G
		expect(keySignature('Dm')).toBe(-1); // relative F
		expect(keySignature('Bbm')).toBe(-5); // relative Db
		expect(keySignature('F#m')).toBe(3); // relative A
	});

	it('rejects a key it does not know rather than guessing', () => {
		expect(() => keySignature('H')).toThrow();
		expect(() => keySignature('')).toThrow();
	});
});

describe('spell — the whole point of this module', () => {
	// Getting this wrong is what makes transposed sheets on other apps read
	// wrong: Gb where F# belongs. Spelling follows the *target key's* position
	// on the circle of fifths, never a fixed table.

	it('spells sharp keys with sharps', () => {
		expect(spell(6, 'G')).toBe('F#'); // G has 1 sharp
		expect(spell(10, 'B')).toBe('A#'); // B has 5 sharps
		expect(spell(3, 'A')).toBe('D#'); // A has 3 sharps
	});

	it('spells flat keys with flats', () => {
		expect(spell(6, 'Db')).toBe('Gb'); // Db has 5 flats
		expect(spell(10, 'F')).toBe('Bb'); // F has 1 flat
		expect(spell(3, 'Eb')).toBe('Eb'); // Eb has 3 flats
	});

	it('gives the SAME pitch opposite spellings in opposite keys', () => {
		// The single most important property in this file.
		expect(spell(6, 'G')).toBe('F#');
		expect(spell(6, 'Db')).toBe('Gb');
		expect(spell(1, 'D')).toBe('C#');
		expect(spell(1, 'Ab')).toBe('Db');
	});

	it('treats C major as neutral and uses sharps', () => {
		expect(spell(6, 'C')).toBe('F#');
		expect(spell(1, 'C')).toBe('C#');
	});

	it('follows a minor key by its own signature, not its letter', () => {
		expect(spell(1, 'Bbm')).toBe('Db'); // Bbm = 5 flats
		expect(spell(1, 'Bm')).toBe('C#'); // Bm  = 2 sharps
		expect(spell(8, 'F#m')).toBe('G#'); // F#m = 3 sharps
		expect(spell(8, 'Fm')).toBe('Ab'); // Fm  = 4 flats
	});

	it('leaves naturals alone in every key', () => {
		for (const key of ['C', 'G', 'F', 'Db', 'F#', 'Am', 'Ebm']) {
			expect(spell(0, key)).toBe('C');
			expect(spell(4, key)).toBe('E');
			expect(spell(11, key)).toBe('B');
		}
	});

	it('does not chase theoretical spellings like Cb', () => {
		// Strict theory says pitch 11 is Cb in Gb major, and E# is pitch 5 in
		// F# major. Nobody wants to read a Cb chord on a guitar sheet, so we
		// stop at the twelve practical names. Documented limitation, not a bug.
		expect(spell(11, 'Gb')).toBe('B');
		expect(spell(5, 'F#')).toBe('F');
	});
});
