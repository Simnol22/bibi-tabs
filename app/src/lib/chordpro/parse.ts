/**
 * ChordPro text -> AST.
 *
 * Chords stay as raw strings. Only the player parses them, at render time, so
 * a song that round-trips through here is byte-identical -- which is what lets
 * the edit screen hand you back the source you actually wrote.
 */

export interface Part {
	/** null for text before the first chord. */
	chord: string | null;
	text: string;
}

export type Line =
	| { type: 'directive'; name: string; value: string }
	| { type: 'comment'; text: string }
	| { type: 'empty' }
	| { type: 'lyric'; parts: Part[] };

const DIRECTIVE = /^\{(.+)\}$/;
const CHORD = /\[([^\]]+)\]/g;

export function parse(text: string): Line[] {
	return text.split('\n').map(parseLine);
}

function parseLine(raw: string): Line {
	if (raw === '') return { type: 'empty' };
	// Anchored at column 0, per the format -- an indented # is a lyric, and
	// treating it as one keeps whitespace intact for monospace layout.
	if (raw.startsWith('#')) return { type: 'comment', text: raw.slice(1) };

	const directive = DIRECTIVE.exec(raw.trim());
	if (directive) {
		const inner = directive[1];
		const colon = inner.indexOf(':');
		const name = (colon === -1 ? inner : inner.slice(0, colon)).trim().toLowerCase();
		if (name !== '') {
			return {
				type: 'directive',
				name,
				value: colon === -1 ? '' : inner.slice(colon + 1).trim()
			};
		}
	}

	return { type: 'lyric', parts: splitChords(raw) };
}

function splitChords(raw: string): Part[] {
	const parts: Part[] = [];
	let chord: string | null = null;
	let cursor = 0;

	CHORD.lastIndex = 0;
	let match: RegExpExecArray | null;
	while ((match = CHORD.exec(raw)) !== null) {
		const text = raw.slice(cursor, match.index);
		// Skip the empty run before a line-leading chord, but never drop a part
		// that carries a chord -- '[C] [G]' needs both.
		if (chord !== null || text !== '') parts.push({ chord, text });
		chord = match[1];
		cursor = match.index + match[0].length;
	}

	const tail = raw.slice(cursor);
	if (chord !== null || tail !== '') parts.push({ chord, text: tail });
	return parts;
}
