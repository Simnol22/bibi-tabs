/**
 * Per-device display preferences. Deliberately NOT synced: you want large text
 * on a phone and small on a laptop, so pushing font size between them would be
 * actively wrong. Song-level state (transpose, capo) lives on the song row.
 *
 * `$state` in a .svelte.ts module is Svelte 5's replacement for a writable
 * store -- read `device.fontSize` anywhere and the UI tracks it.
 */

export type Layout = 'flowing' | 'monospace';

interface DevicePrefs {
	fontSize: number;
	layout: Layout;
}

const STORAGE_KEY = 'bibi-tabs.device';
const DEFAULTS: DevicePrefs = { fontSize: 17, layout: 'flowing' };
const MIN_FONT = 12;
const MAX_FONT = 34;

function load(): DevicePrefs {
	if (typeof localStorage === 'undefined') return { ...DEFAULTS };
	try {
		return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}') };
	} catch {
		return { ...DEFAULTS };
	}
}

export const device = $state<DevicePrefs>(load());

function persist(): void {
	localStorage.setItem(STORAGE_KEY, JSON.stringify(device));
}

export function zoom(step: number): void {
	device.fontSize = Math.min(MAX_FONT, Math.max(MIN_FONT, device.fontSize + step));
	persist();
}

export function setLayout(layout: Layout): void {
	device.layout = layout;
	persist();
}
