const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Shorten a URL.
 * @param {string} url
 * @returns {Promise<{ short_url: string, code: string }>}
 */
export async function shortenUrl(url) {
  const formData = new FormData();
  formData.append('url', url);

  const res = await fetch(`${BASE_URL}/shorten`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Failed to shorten URL');
  }

  return res.json();
}

/**
 * Get overall dashboard stats.
 * @returns {Promise<{ total_urls: number, total_clicks: number, clicks_today: number, top_urls: Array }>}
 */
export async function getDashboard() {
  const res = await fetch(`${BASE_URL}/analytics/dashboard`);
  if (!res.ok) throw new Error('Failed to load dashboard data');
  return res.json();
}

/**
 * Get per-URL analytics.
 * @param {string} code
 * @returns {Promise<object>}
 */
export async function getUrlStats(code) {
  const res = await fetch(`${BASE_URL}/analytics/${code}`);
  if (!res.ok) throw new Error(`No analytics found for /${code}`);
  return res.json();
}
