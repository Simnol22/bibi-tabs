import { describe, it, expect } from 'vitest';
import { parseChord, formatChord } from './chord';

describe('parseChord — roots and qualities', () => {
	it('parses a bare major triad', () => {
		expect(parseChord('C')).toEqual({ root: 'C', quality: '', ext: '', bass: null });
	});

	it('parses accidentals in the root', () => {
		expect(parseChord('F#')?.root).toBe('F#');
		expect(parseChord('Bb')?.root).toBe('Bb');
	});

	it('normalises unicode accidentals', () => {
		expect(parseChord('F♯m')?.root).toBe('F#');
		expect(parseChord('B♭')?.root).toBe('Bb');
	});

	it('separates quality from extension', () => {
		expect(parseChord('Cm')).toEqual({ root: 'C', quality: 'm', ext: '', bass: null });
		expect(parseChord('Cm7')).toEqual({ root: 'C', quality: 'm', ext: '7', bass: null });
		expect(parseChord('C7')).toEqual({ root: 'C', quality: '', ext: '7', bass: null });
		expect(parseChord('Cmaj7')).toEqual({ root: 'C', quality: 'maj', ext: '7', bass: null });
	});

	it('does not mistake the m in maj for a minor marker', () => {
		expect(parseChord('Cmaj7')?.quality).toBe('maj');
		expect(parseChord('Cmin7')?.quality).toBe('min');
	});

	it('accepts the alternative quality spellings people actually type', () => {
		expect(parseChord('C-7')?.quality).toBe('-'); // minor
		expect(parseChord('C+')?.quality).toBe('+'); // augmented
		expect(parseChord('Caug')?.quality).toBe('aug');
		expect(parseChord('Cdim7')?.quality).toBe('dim');
		expect(parseChord('C°')?.quality).toBe('°');
		expect(parseChord('Cø7')?.quality).toBe('ø');
	});

	it('keeps the extension verbatim, however baroque', () => {
		expect(parseChord('Csus4')?.ext).toBe('sus4');
		expect(parseChord('C7sus4')?.ext).toBe('7sus4');
		expect(parseChord('Cadd9')?.ext).toBe('add9');
		expect(parseChord('Bbmaj7#11')?.ext).toBe('7#11');
		expect(parseChord('C7b9')?.ext).toBe('7b9');
		expect(parseChord('G5')?.ext).toBe('5');
	});
});

describe('parseChord — slash chords', () => {
	it('splits the bass note off', () => {
		expect(parseChord('C/G')).toEqual({ root: 'C', quality: '', ext: '', bass: 'G' });
	});

	it('handles a bass under a complicated chord', () => {
		expect(parseChord('F#m7b5/A')).toEqual({
			root: 'F#',
			quality: 'm',
			ext: '7b5',
			bass: 'A'
		});
	});

	it('accepts an accidental in the bass', () => {
		expect(parseChord('Bb/D')?.bass).toBe('D');
		expect(parseChord('D/F#')?.bass).toBe('F#');
		expect(parseChord('Am/G#')?.bass).toBe('G#');
	});

	it('reports no bass rather than an empty one', () => {
		expect(parseChord('Am7')?.bass).toBeNull();
	});

	it('rejects a malformed slash', () => {
		expect(parseChord('C/')).toBeNull();
		expect(parseChord('/G')).toBeNull();
		expect(parseChord('C/H')).toBeNull(); // H is not a note here
		expect(parseChord('C/G/E')).toBeNull();
	});
});

describe('parseChord — rejecting things that are not chords', () => {
	// The chord-line heuristic in import/text.ts leans entirely on this
	// returning null for ordinary words. False positives there corrupt lyrics.

	it('rejects words that merely start with a note letter', () => {
		for (const word of ['Chorus', 'Bass', 'Dad', 'Ace', 'Age', 'Face', 'Bad', 'Cave']) {
			expect(parseChord(word)).toBeNull();
		}
	});

	it('rejects section headers and non-chord markers', () => {
		for (const token of ['[Chorus]', 'Verse', '1:', 'N.C.', '|', '', '   ']) {
			expect(parseChord(token)).toBeNull();
		}
	});

	it('rejects solfège, which would otherwise shadow real note letters', () => {
		for (const word of ['Do', 'Re', 'Mi', 'Fa', 'Sol', 'La', 'Si']) {
			expect(parseChord(word)).toBeNull();
		}
	});

	it('accepts Am even though it is also a word — the heuristic handles that', () => {
		expect(parseChord('Am')).not.toBeNull();
	});
});

describe('formatChord', () => {
	it('round-trips every shape we parse', () => {
		for (const s of ['C', 'Cm', 'Cmaj7', 'F#m7b5/A', 'Bb/D', 'C7sus4', 'C°', 'G5', 'C-7']) {
			const chord = parseChord(s);
			expect(chord).not.toBeNull();
			expect(formatChord(chord!)).toBe(s);
		}
	});

	it('normalises unicode accidentals on the way out', () => {
		expect(formatChord(parseChord('F♯m7')!)).toBe('F#m7');
	});
});
