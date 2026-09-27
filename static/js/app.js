// ResQGrid shared client helpers.
// The emergency detail page contains its map-specific code inline.
function refreshResourceData() {
  return fetch('/api/resources').then(r => r.json());
}
