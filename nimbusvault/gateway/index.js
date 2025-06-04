const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

const services = {
  auth: process.env.AUTH_SERVICE_URL || 'http://auth-service:8001/health',
  upload: process.env.UPLOAD_SERVICE_URL || 'http://upload-service:8002/health',
  metadata: process.env.METADATA_SERVICE_URL || 'http://metadata-service:8003/health',
};

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.get('/health', async (req, res) => {
  const results = {};

  await Promise.all(
    Object.entries(services).map(async ([name, url]) => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2000);
      try {
        const response = await fetch(url, { signal: controller.signal });
        results[name] = response.ok ? 'healthy' : 'unhealthy';
      } catch (err) {
        results[name] = 'unhealthy';
      } finally {
        clearTimeout(timeout);
      }
    })
  );

  const overall = Object.values(results).every((s) => s === 'healthy')
    ? 'healthy'
    : 'unhealthy';

  res.json({ status: overall, services: results });
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
