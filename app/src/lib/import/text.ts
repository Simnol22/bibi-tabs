/**
 * Chord-over-lyric text -> ChordPro.
 *
 * This is the foundation, not a fallback. Pasting works on any site forever,
 * and it is what every scraping adapter funnels through -- so when Ultimate
 * Guitar redesigns, this still works.
 *
 *   C          G                 [C]Yesterday, [G]all my
 *   Yesterday, all my       ->
 */

import { parseChord } from '../music/chord';

const TAB_WIDTH = 8;
const CHORD_LINE_THRESHOLD = 0.8;
const BRACKETED = /^\[([^\]]+)\]$/;

/**
 * A line is a chord line when at least 80% of its tokens parse as chords.
 *
 * The threshold exists because real sheets put stray marks on chord lines --
 * 'x4', '|', an annotation. Requiring every token to parse would reject them.
 */
export function isChordLine(line: string): boolean {
	const tokens = line.trim().split(/\s+/).filter((token) => token !== '');
	if (tokens.length === 0) return false;
	const chords = tokens.filter((token) => parseChord(token) !== null).length;
	return chords / tokens.length >= CHORD_LINE_THRESHOLD;
}

export function textToChordPro(text: string): string {
	const lines = text.split('\n').map(expandTabs);
	const out: string[] = [];

	for (let i = 0; i < lines.length; i++) {
		const line = lines[i];

		if (!isChordLine(line)) {
			out.push(sectionHeader(line) ?? line);
			continue;
		}

		// Pair with the line below, unless it is blank or is itself chords.
		const next = lines[i + 1];
		const lyric = next !== undefined && next.trim() !== '' && !isChordLine(next) ? next : null;
		out.push(merge(line, lyric ?? ''));
		if (lyric !== null) i++;
	}

	return out.join('\n');
}

/** `[Chorus]` would otherwise parse as a chord named "Chorus". */
function sectionHeader(line: string): string | null {
	const bracketed = BRACKETED.exec(line.trim());
	if (!bracketed || parseChord(bracketed[1]) !== null) return null;
	return `{comment: ${bracketed[1].trim()}}`;
}

/** Tab stops matter: columns are how a chord finds its syllable. */
function expandTabs(line: string): string {
	let out = '';
	for (const char of line) {
		out += char === '\t' ? ' '.repeat(TAB_WIDTH - (out.length % TAB_WIDTH)) : char;
	}
	return out;
}

/**
 * Drop each chord into the lyric at the column it was written above.
 *
 * Right to left, so an insertion never shifts the columns still to be placed.
 * A chord past the end of the lyric pads rather than snapping to the last
 * syllable -- it usually marks a turnaround after the words stop.
 */
function merge(chordLine: string, lyric: string): string {
	let out = lyric;

	for (const { chord, column } of chordsWithColumns(chordLine).reverse()) {
		const padded = column > out.length ? out.padEnd(column) : out;
		out = `${padded.slice(0, column)}[${chord}]${padded.slice(column)}`;
	}
	return out;
}

function chordsWithColumns(line: string): { chord: string; column: number }[] {
	const found: { chord: string; column: number }[] = [];
	const token = /\S+/g;

	let match: RegExpExecArray | null;
	while ((match = token.exec(line)) !== null) {
		if (parseChord(match[0]) !== null) found.push({ chord: match[0], column: match.index });
	}
	return found;
}
