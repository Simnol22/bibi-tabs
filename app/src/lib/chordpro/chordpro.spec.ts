import { describe, it, expect } from 'vitest';
import { parse } from './parse';
import { serialize } from './serialize';

describe('parse — directives', () => {
	it('reads a directive with a value', () => {
		expect(parse('{title: Yesterday}')).toEqual([
			{ type: 'directive', name: 'title', value: 'Yesterday' }
		]);
	});

	it('reads a directive with no value', () => {
		expect(parse('{soc}')).toEqual([{ type: 'directive', name: 'soc', value: '' }]);
	});

	it('is indifferent to spacing and case, as the format is', () => {
		expect(parse('{Title:Yesterday}')).toEqual([
			{ type: 'directive', name: 'title', value: 'Yesterday' }
		]);
		expect(parse('  {artist:  The Beatles  }  ')).toEqual([
			{ type: 'directive', name: 'artist', value: 'The Beatles' }
		]);
	});

	it('splits on the first colon only', () => {
		expect(parse('{comment: verse 2: quieter}')).toEqual([
			{ type: 'directive', name: 'comment', value: 'verse 2: quieter' }
		]);
	});

	it('treats an empty brace as ordinary text', () => {
		expect(parse('{}')).toEqual([{ type: 'lyric', parts: [{ chord: null, text: '{}' }] }]);
	});
});

describe('parse — lines', () => {
	it('reads a blank line as blank', () => {
		expect(parse('')).toEqual([{ type: 'empty' }]);
	});

	it('reads a # line as a comment', () => {
		expect(parse('# not shown to the player')).toEqual([
			{ type: 'comment', text: ' not shown to the player' }
		]);
	});

	it('reads a lyric with no chords', () => {
		expect(parse('Yesterday')).toEqual([
			{ type: 'lyric', parts: [{ chord: null, text: 'Yesterday' }] }
		]);
	});

	it('splits chords out of a lyric', () => {
		expect(parse('[C]Yesterday, [G]all my')).toEqual([
			{
				type: 'lyric',
				parts: [
					{ chord: 'C', text: 'Yesterday, ' },
					{ chord: 'G', text: 'all my' }
				]
			}
		]);
	});

	it('handles a lyric that starts before the first chord', () => {
		expect(parse('Hello [C]world')).toEqual([
			{
				type: 'lyric',
				parts: [
					{ chord: null, text: 'Hello ' },
					{ chord: 'C', text: 'world' }
				]
			}
		]);
	});

	it('handles a chord with nothing after it', () => {
		expect(parse('Hello [C]')).toEqual([
			{
				type: 'lyric',
				parts: [
					{ chord: null, text: 'Hello ' },
					{ chord: 'C', text: '' }
				]
			}
		]);
	});

	it('handles a line of chords with no lyric — an instrumental break', () => {
		expect(parse('[C] [G] [Am]')).toEqual([
			{
				type: 'lyric',
				parts: [
					{ chord: 'C', text: ' ' },
					{ chord: 'G', text: ' ' },
					{ chord: 'Am', text: '' }
				]
			}
		]);
	});

	it('leaves an unclosed bracket as literal text', () => {
		expect(parse('[C major chord')).toEqual([
			{ type: 'lyric', parts: [{ chord: null, text: '[C major chord' }] }
		]);
	});

	it('preserves whitespace exactly, because monospace layout depends on it', () => {
		const line = '   two   spaces   everywhere   ';
		expect(parse(line)).toEqual([{ type: 'lyric', parts: [{ chord: null, text: line }] }]);
	});

	it('reads a multi-line song in order', () => {
		const song = parse('{title: X}\n\n[C]One\nTwo');
		expect(song.map((l) => l.type)).toEqual(['directive', 'empty', 'lyric', 'lyric']);
	});
});

describe('serialize', () => {
	it('round-trips canonical text byte for byte', () => {
		const source = [
			'{title: Yesterday}',
			'{artist: The Beatles}',
			'{soc}',
			'',
			'# a note to self',
			'[F]Yester[Em7]day, [A7]all my [Dm]troubles seemed so far a[Bb]way',
			'Now it looks as though [C7]they are here to stay',
			'[C] [G] [Am]',
			'{eoc}'
		].join('\n');
		expect(serialize(parse(source))).toBe(source);
	});

	it('normalises messy input and is then stable', () => {
		const messy = '{Title:Yesterday}\n{ARTIST:  The Beatles }';
		const once = serialize(parse(messy));
		expect(once).toBe('{title: Yesterday}\n{artist: The Beatles}');
		expect(serialize(parse(once))).toBe(once);
	});

	it('preserves the original whitespace of a lyric line', () => {
		const source = 'a   b\t\tc   ';
		expect(serialize(parse(source))).toBe(source);
	});

	it('survives a song with no trailing newline and one with', () => {
		expect(serialize(parse('[C]One'))).toBe('[C]One');
		expect(serialize(parse('[C]One\n'))).toBe('[C]One\n');
	});
});
