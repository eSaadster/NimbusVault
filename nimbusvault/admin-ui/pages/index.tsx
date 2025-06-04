import { useEffect, useState } from 'react';

export default function Home() {
  const [health, setHealth] = useState<string>('Loading...');

  useEffect(() => {
    fetch('/api/metadata/health')
      .then(async (res) => {
        if (!res.ok) throw new Error('Failed to fetch');
        try {
          const data = await res.json();
          return JSON.stringify(data, null, 2);
        } catch {
          return res.text();
        }
      })
      .then((text) => setHealth(text))
      .catch(() => setHealth('Error fetching health'));
  }, []);

  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>NimbusVault Admin UI</h1>
      <pre>{health}</pre>
    </main>
  );
}
