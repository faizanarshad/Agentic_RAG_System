// Opening a workspace on a specific tab, e.g. /workspace/engineering?view=compare (links from the website).
// Workspaces render client-side only, so reading the URL during the first render is safe.
export function initialView(allowed, fallback) {
  if (typeof window === 'undefined') return fallback;
  const requested = new URLSearchParams(window.location.search).get('view');
  return allowed.includes(requested) ? requested : fallback;
}
