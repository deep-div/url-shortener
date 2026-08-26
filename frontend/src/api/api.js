export async function shortenUrl(url) {
  const formData = new FormData();
  formData.append('url', url);

  const res = await fetch('/v1/shorten', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Failed to shorten URL');
  }

  return res.json();
}

export async function getUrlStats(code) {
  const res = await fetch(`/v1/analytics/${code}`);
  if (res.status === 429) throw new Error('Too many requests — please wait a moment and try again');
  if (res.status === 404) throw new Error(`No analytics found for /${code}`);
  if (!res.ok) throw new Error(`Failed to load analytics (${res.status})`);
  return res.json();
}
