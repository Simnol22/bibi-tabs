import { describe, it, expect } from 'vitest';
import { isChordLine, textToChordPro } from './text';

describe('isChordLine', () => {
	it('accepts a line that is all chords', () => {
		expect(isChordLine('C G Am F')).toBe(true);
		expect(isChordLine('  F#m7b5/A   Bb   ')).toBe(true);
		expect(isChordLine('C')).toBe(true);
	});

	it('rejects a lyric', () => {
		expect(isChordLine('Yesterday, all my troubles seemed so far away')).toBe(false);
		expect(isChordLine('Now it looks as though')).toBe(false);
	});

	it('rejects blank lines', () => {
		expect(isChordLine('')).toBe(false);
		expect(isChordLine('     ')).toBe(false);
	});

	it('rejects section headers', () => {
		expect(isChordLine('[Chorus]')).toBe(false);
		expect(isChordLine('Verse 1:')).toBe(false);
		expect(isChordLine('Intro')).toBe(false);
	});

	it('holds the threshold at exactly 80 percent', () => {
		expect(isChordLine('C G Am hey')).toBe(false); // 3/4 = 0.75
		expect(isChordLine('C G Am F hey')).toBe(true); // 4/5 = 0.80
	});

	it('does not care whether columns are tabs or spaces', () => {
		expect(isChordLine('C\tG\tAm')).toBe(true);
	});
});

describe('textToChordPro', () => {
	it('pairs a chord line with the lyric beneath it', () => {
		// G sits over 'all' (col 11), Am over 'troubles' (18), F over 'seemed' (27).
		const source = [
			'C          G      Am       F',
			'Yesterday, all my troubles seemed so far away'
		].join('\n');
		expect(textToChordPro(source)).toBe(
			'[C]Yesterday, [G]all my [Am]troubles [F]seemed so far away'
		);
	});

	it('leaves a lyric with no chords above it alone', () => {
		expect(textToChordPro('Just a line of words')).toBe('Just a line of words');
	});

	it('keeps a chord line that has no lyric under it — an instrumental break', () => {
		// Padded to the original columns rather than collapsed to single spaces:
		// on an instrumental line the width of a gap is the timing.
		expect(textToChordPro('C   G')).toBe('[C]    [G]');
		expect(textToChordPro('C   G\n\nnext')).toBe('[C]    [G]\n\nnext');
	});

	it('does not pair two chord lines with each other', () => {
		expect(textToChordPro('C G\nAm F')).toBe('[C]  [G]\n[Am]   [F]');
	});

	it('holds a chord that sits past the end of the lyric in place', () => {
		// A turnaround after the words stop. Dropping it onto the last syllable
		// would put it in the wrong bar.
		expect(textToChordPro('C        G\nHello')).toBe('[C]Hello    [G]');
	});

	it('expands tabs so columns line up before pairing', () => {
		expect(textToChordPro('C\tG\nHello   world')).toBe('[C]Hello   [G]world');
	});

	it('turns a bracketed section header into a comment', () => {
		// Passing [Chorus] through verbatim would make ChordPro read it as a
		// chord named "Chorus" -- corruption, not just ugliness.
		expect(textToChordPro('[Chorus]')).toBe('{comment: Chorus}');
		expect(textToChordPro('[Intro]\nC G')).toBe('{comment: Intro}\n[C]  [G]');
	});

	it('leaves a bracketed real chord alone', () => {
		expect(textToChordPro('[C]')).toBe('[C]');
	});

	it('preserves blank lines between stanzas', () => {
		expect(textToChordPro(['C', 'One', '', 'G', 'Two'].join('\n'))).toBe('[C]One\n\n[G]Two');
	});

	it('converts a whole song', () => {
		const source = [
			'[Verse 1]',
			'C          G',
			'Yesterday, all my',
			'',
			'Am       F',
			'troubles seemed so'
		].join('\n');
		expect(textToChordPro(source)).toBe(
			['{comment: Verse 1}', '[C]Yesterday, [G]all my', '', '[Am]troubles [F]seemed so'].join('\n')
		);
	});
});
