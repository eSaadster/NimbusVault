const express = require('express');
const fetch = require('node-fetch');
const client = require('prom-client');

const app = express();
const PORT = process.env.PORT || 3000;

const register = new client.Registry();
client.collectDefaultMetrics({ register });
const httpRequestDuration = new client.Histogram({
  name: 'gateway_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'code'],
});
register.registerMetric(httpRequestDuration);

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer({ method: req.method, route: req.path });
  res.on('finish', () => {
    end({ code: res.statusCode });
  });
  next();
});

app.get('/metrics', async (_, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.get('/health/live', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/health/ready', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/health/detailed', async (req, res) => {
  const services = {
    'auth-service': 'http://auth-service:8001/health/ready',
    'upload-service': 'http://upload-service:8002/health/ready',
    'metadata-service': 'http://metadata-service:8003/health/ready',
    'admin-ui': 'http://admin-ui:3001/api/health/ready'
  };
  const results = {};
  for (const [name, url] of Object.entries(services)) {
    const start = Date.now();
    try {
      const resp = await fetch(url, { timeout: 500 });
      results[name] = { status: resp.ok ? 'ok' : 'error', responseTime: Date.now() - start };
    } catch (e) {
      results[name] = { status: 'error', responseTime: Date.now() - start };
    }
  }
  const allOk = Object.values(results).every(r => r.status === 'ok');
  res.status(allOk ? 200 : 503).json({ status: allOk ? 'ok' : 'error', services: results });
});

app.get('/health/status', async (req, res) => {
  const start = Date.now();
  const response = await fetch(`http://localhost:${PORT}/health/detailed`).then(r => r.json());
  const totalTime = Date.now() - start;
  res.status(response.status === 'ok' ? 200 : 503).json({ ...response, totalTime });
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
