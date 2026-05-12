// Preload script — runs in renderer context before web content loads.
// Currently minimal; extend for IPC when adding native features.

window.addEventListener('DOMContentLoaded', () => {
  console.log('[Preload] Bioinfo Assistant ready');
});
