const BASE_URL = import.meta.env.VITE_API_URL ?? '';

export async function shortenUrl(url) {
  const formData = new FormData();
  formData.append('url', url);

  const res = await fetch(`${BASE_URL}/v1/shorten`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Failed to shorten URL');
  }

  return res.json();
}

export async function getUrlStats(code, { from, to } = {}) {
  const params = new URLSearchParams();
  if (from) params.set('from', from);
  if (to) params.set('to', to);
  const query = params.toString() ? `?${params}` : '';
  const res = await fetch(`${BASE_URL}/v1/analytics/${code}${query}`);
  if (!res.ok) throw new Error(`No analytics found for /${code}`);
  return res.json();
}
