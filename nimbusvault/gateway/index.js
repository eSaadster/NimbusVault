const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const http = require('http');

const app = express();
const PORT = process.env.PORT || 3000;

// Simple request logger
app.use((req, res, next) => {
  console.log(`${req.method} ${req.originalUrl}`);
  next();
});

// Basic CORS middleware
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Proxy helper
const proxy = (path, target) =>
  createProxyMiddleware({
    target,
    changeOrigin: true,
    pathRewrite: (pathReq) => pathReq.replace(new RegExp(`^${path}`), ''),
    onError: (_err, _req, res) => {
      res.status(502).json({ error: 'Bad gateway' });
    },
    logLevel: 'warn',
  });

// Proxy routes for microservices
app.use('/api/auth', proxy('/api/auth', 'http://auth-service:8001'));
app.use('/api/upload', proxy('/api/upload', 'http://upload-service:8002'));
app.use('/api/metadata', proxy('/api/metadata', 'http://metadata-service:8003'));
app.use('/api/storage', proxy('/api/storage', 'http://storage-service:8004'));

// Health check endpoint
const services = {
  auth: { host: 'auth-service', port: 8001 },
  upload: { host: 'upload-service', port: 8002 },
  metadata: { host: 'metadata-service', port: 8003 },
  storage: { host: 'storage-service', port: 8004 },
};

function checkService({ host, port }) {
  return new Promise((resolve) => {
    const req = http.get({ host, port, timeout: 2000 }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

app.get('/health', async (_req, res) => {
  const status = {};
  await Promise.all(
    Object.entries(services).map(async ([name, conf]) => {
      status[name] = await checkService(conf);
    })
  );
  res.json(status);
});

// Default route
app.get('/', (_req, res) => {
  res.send('Hello from gateway');
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found' });
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
