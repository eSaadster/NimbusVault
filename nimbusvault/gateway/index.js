const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = 8000;

// Health check route
app.get('/health', (req, res) => {
  res.json({ service: 'gateway', status: 'OK' });
});

// Proxy routes to other services
app.use(
  '/api/auth',
  createProxyMiddleware({ target: 'http://auth-service:8001', changeOrigin: true })
);
app.use(
  '/api/upload',
  createProxyMiddleware({ target: 'http://upload-service:8002', changeOrigin: true })
);
app.use(
  '/api/storage',
  createProxyMiddleware({ target: 'http://storage-service:8003', changeOrigin: true })
);
app.use(
  '/api/metadata',
  createProxyMiddleware({ target: 'http://metadata-service:8004', changeOrigin: true })
);

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
