import { useEffect } from 'react';
import { useParams } from 'react-router-dom';

export default function RedirectPage() {
  const { code } = useParams();

  useEffect(() => {
    async function redirect() {
      let ipv4 = '';
      let ipv6 = '';
      try {
        const [res4, res6] = await Promise.all([
          fetch('https://api.ipify.org?format=json'),
          fetch('https://api64.ipify.org?format=json'),
        ]);
        const [data4, data6] = await Promise.all([res4.json(), res6.json()]);
        ipv4 = data4.ip || '';
        ipv6 = data6.ip || '';
      } catch {
        // proceed without IPs, backend will detect from headers
      }

      try {
        const params = new URLSearchParams({ ipv4, ipv6 });
        const res = await fetch(`/v1/resolve/${code}?${params}`);
        if (!res.ok) {
          window.location.href = '/';
          return;
        }
        const { long_url } = await res.json();
        window.location.href = long_url;
      } catch {
        window.location.href = '/';
      }
    }
    redirect();
  }, [code]);

  return null;
}
