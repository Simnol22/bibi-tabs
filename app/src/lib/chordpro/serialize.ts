/**
 * AST -> ChordPro text.
 *
 * Canonical input comes back byte for byte. Messy input is normalised once
 * (directive spacing and case) and is stable from then on.
 */

import type { Line } from './parse';

export function serialize(lines: Line[]): string {
	return lines.map(serializeLine).join('\n');
}

function serializeLine(line: Line): string {
	switch (line.type) {
		case 'empty':
			return '';
		case 'comment':
			return `#${line.text}`;
		case 'directive':
			return line.value === '' ? `{${line.name}}` : `{${line.name}: ${line.value}}`;
		case 'lyric':
			return line.parts
				.map((part) => (part.chord === null ? '' : `[${part.chord}]`) + part.text)
				.join('');
	}
}
