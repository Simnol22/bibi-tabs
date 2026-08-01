// The library lives in IndexedDB in the browser, so there is nothing for the
// server to render and no way to enumerate /song/[id] at build time.
// This makes the app a pure SPA served from a static fallback shell.
export const ssr = false;
