import { describe, it, expect } from 'vitest';
import { fingerings } from './guitar';

describe('fingerings', () => {
	it('finds the open shape for a plain triad', () => {
		const c = fingerings('C');
		expect(c.length).toBeGreaterThan(1); // alternate voicings exist
		expect(c[0]).toMatchObject({ frets: [-1, 3, 2, 0, 1, 0], baseFret: 1 });
	});

	it('finds minor, seventh and extended shapes', () => {
		for (const token of ['Am', 'Cm7', 'G7', 'Fmaj7', 'Dsus4', 'Eadd9', 'Bdim', 'Caug']) {
			expect(fingerings(token).length, token).toBeGreaterThan(0);
		}
	});

	it('reads a barre chord as a barre', () => {
		const f = fingerings('F')[0];
		expect(f.barres?.length).toBeGreaterThan(0);
	});

	it('treats enharmonic roots as the same chord', () => {
		expect(fingerings('Db')).toEqual(fingerings('C#'));
		expect(fingerings('Gb')).toEqual(fingerings('F#'));
		expect(fingerings('D#m')).toEqual(fingerings('Ebm'));
	});

	it('accepts the alternative quality spellings the parser allows', () => {
		expect(fingerings('C-7')).toEqual(fingerings('Cm7'));
		expect(fingerings('C+')).toEqual(fingerings('Caug'));
		expect(fingerings('C°')).toEqual(fingerings('Cdim'));
	});

	it('finds a slash chord that the dataset knows', () => {
		expect(fingerings('C/G').length).toBeGreaterThan(0);
		expect(fingerings('D/F#').length).toBeGreaterThan(0);
	});

	it('falls back to the base chord when the exact bass is unknown', () => {
		// Better to show the F#m7b5 shape than an empty box.
		expect(fingerings('F#m7b5/A')).toEqual(fingerings('F#m7b5'));
	});

	it('returns nothing for something that is not a chord', () => {
		expect(fingerings('N.C.')).toEqual([]);
		expect(fingerings('Chorus')).toEqual([]);
		expect(fingerings('')).toEqual([]);
	});

	it('returns nothing rather than guessing at a chord it lacks', () => {
		expect(fingerings('Cmaj7b13')).toEqual([]);
	});

	it('gives every root a plain major and minor shape', () => {
		for (const root of ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']) {
			expect(fingerings(root).length, root).toBeGreaterThan(0);
			expect(fingerings(`${root}m`).length, `${root}m`).toBeGreaterThan(0);
		}
	});
});
