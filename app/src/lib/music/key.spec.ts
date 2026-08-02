import { describe, it, expect } from 'vitest';
import { detectKey } from './key';

describe('detectKey', () => {
	it('finds a major key from its diatonic chords', () => {
		expect(detectKey(['C', 'F', 'G', 'C'])).toBe('C');
		expect(detectKey(['G', 'C', 'D', 'G'])).toBe('G');
		expect(detectKey(['D', 'G', 'A', 'D'])).toBe('D');
		expect(detectKey(['A', 'D', 'E', 'A'])).toBe('A');
	});

	it('finds a flat key', () => {
		expect(detectKey(['F', 'Bb', 'C', 'F'])).toBe('F');
		expect(detectKey(['Bb', 'Eb', 'F', 'Bb'])).toBe('Bb');
	});

	it('finds a minor key', () => {
		expect(detectKey(['Am', 'Dm', 'Em', 'Am'])).toBe('Am');
		expect(detectKey(['Em', 'Am', 'Bm', 'Em'])).toBe('Em');
	});

	it('accepts the major V of a minor key, which is how minor songs actually go', () => {
		// A major E chord in A minor is the harmonic-minor V. Refusing it would
		// push half the minor repertoire into the wrong key.
		expect(detectKey(['Am', 'Dm', 'E', 'Am'])).toBe('Am');
		expect(detectKey(['Am', 'F', 'C', 'E7', 'Am'])).toBe('Am');
	});

	it('resolves an ambiguous chord set by where the song starts and ends', () => {
		// G C D Em is diatonic to both G major and E minor; landing on Em first
		// and never touching G as a tonic makes it E minor.
		expect(detectKey(['Em', 'C', 'G', 'D'])).toBe('Em');
		expect(detectKey(['G', 'C', 'D', 'Em', 'G'])).toBe('G');
	});

	it('handles a real song with borrowed chords', () => {
		// Yesterday: the Em7 and A7 are outside F major, and it is still in F.
		expect(detectKey(['F', 'Em7', 'A7', 'Dm', 'Bb', 'C7', 'F'])).toBe('F');
	});

	it('ignores tokens that are not chords', () => {
		expect(detectKey(['N.C.', 'C', 'F', 'G', 'C'])).toBe('C');
		expect(detectKey(['|', '%'])).toBeNull();
	});

	it('has nothing to say about an empty song', () => {
		expect(detectKey([])).toBeNull();
	});

	it('names the key the way the rest of the app spells keys', () => {
		// Comes back as a key name transposeKey and spell both accept.
		expect(detectKey(['Eb', 'Ab', 'Bb', 'Eb'])).toBe('Eb');
	});
});
