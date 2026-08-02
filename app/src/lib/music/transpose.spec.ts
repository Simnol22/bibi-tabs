import { describe, it, expect } from 'vitest';
import { transpose, transposeKey } from './transpose';

describe('transpose', () => {
	it('shifts a plain triad', () => {
		expect(transpose('C', 2, 'D')).toBe('D');
		expect(transpose('G', 2, 'A')).toBe('A');
	});

	it('carries quality and extension through untouched', () => {
		expect(transpose('Cm7', 2, 'D')).toBe('Dm7');
		expect(transpose('Cmaj7#11', 2, 'D')).toBe('Dmaj7#11');
		expect(transpose('C7sus4', 5, 'F')).toBe('F7sus4');
	});

	it('wraps around the octave', () => {
		expect(transpose('B', 2, 'C#')).toBe('C#');
		expect(transpose('A', 3, 'C')).toBe('C');
	});

	it('shifts downwards', () => {
		expect(transpose('C', -1, 'B')).toBe('B');
		expect(transpose('C', -2, 'Bb')).toBe('Bb');
	});

	it('spells the result from the target key, not the source', () => {
		// Same pitch, two keys, two spellings. This is the payoff of spelling.ts.
		expect(transpose('C', 6, 'F#')).toBe('F#');
		expect(transpose('C', 6, 'Gb')).toBe('Gb');
	});

	it('respells without shifting when given zero semitones', () => {
		// Opening a sheet written in sharps while displaying a flat key should
		// still read correctly, even with the transpose knob at zero.
		expect(transpose('C#', 0, 'Db')).toBe('Db');
		expect(transpose('Gb', 0, 'D')).toBe('F#');
	});

	it('leaves a token it cannot parse completely alone', () => {
		// Import output contains section markers and the occasional 'N.C.'.
		// Mangling them would be worse than passing them through.
		expect(transpose('N.C.', 2, 'D')).toBe('N.C.');
		expect(transpose('%', 2, 'D')).toBe('%');
	});
});

describe('transpose — slash chords', () => {
	it('shifts root and bass together', () => {
		expect(transpose('C/E', 5, 'F')).toBe('F/A');
		expect(transpose('D/F#', -2, 'C')).toBe('C/E');
		expect(transpose('G/B', 1, 'Ab')).toBe('Ab/C');
	});

	it('spells the bass from the target key too', () => {
		expect(transpose('Bb/D', -1, 'A')).toBe('A/C#');
		expect(transpose('C/E', 1, 'Db')).toBe('Db/F');
	});

	it('keeps a complicated chord intact across the shift', () => {
		// Transposing F#m up a semitone lands in Gm, which has two flats — so
		// the bass reads Bb. Pass the key the song is actually in and the
		// spelling follows.
		expect(transpose('F#m7b5/A', 1, 'Gm')).toBe('Gm7b5/Bb');
	});

	it('spells strictly by the key it is given, for better or worse', () => {
		// The same shift told it is heading for G major spells that bass A#.
		// Key-driven spelling is the rule; choosing a sensible target key is
		// the caller's job.
		expect(transpose('F#m7b5/A', 1, 'G')).toBe('Gm7b5/A#');
	});

	it('does not invent a bass where there was none', () => {
		expect(transpose('Am7', 2, 'B')).toBe('Bm7');
	});
});

describe('transposeKey', () => {
	it('shifts a major key', () => {
		expect(transposeKey('C', 2)).toBe('D');
		expect(transposeKey('G', 5)).toBe('C');
	});

	it('keeps a minor key minor', () => {
		expect(transposeKey('Am', 2)).toBe('Bm');
		expect(transposeKey('F#m', 1)).toBe('Gm');
	});

	it('prefers the spelling with fewer accidentals', () => {
		// A# major would need ten sharps; Bb needs two.
		expect(transposeKey('A', 1)).toBe('Bb');
		// Db (5 flats) over C# (7 sharps).
		expect(transposeKey('C', 1)).toBe('Db');
	});

	it('breaks a tie by keeping the direction the source key was already going', () => {
		// F# and Gb are both six accidentals. F is a flat key, so go to Gb.
		expect(transposeKey('F', 1)).toBe('Gb');
		// B is a sharp key, so go to F#.
		expect(transposeKey('B', 7)).toBe('F#');
	});

	it('wraps around the octave', () => {
		expect(transposeKey('B', 1)).toBe('C');
		expect(transposeKey('C', -1)).toBe('B');
		expect(transposeKey('C', 12)).toBe('C');
	});
});
