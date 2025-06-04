const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS for all routes
app.use(cors());

// Common error handler for proxy failures
const proxyErrorHandler = (err, req, res) => {
  console.error('Proxy error:', err);
  if (!res.headersSent) {
    res.status(500).json({ error: 'Proxy error' });
  }
};

// Route: /auth/* -> http://auth-service:8001
app.use(
  '/auth',
  createProxyMiddleware({
    target: 'http://auth-service:8001',
    changeOrigin: true,
    pathRewrite: { '^/auth': '' },
    onError: proxyErrorHandler,
  })
);

// Route: /upload/* -> http://upload-service:8002
app.use(
  '/upload',
  createProxyMiddleware({
    target: 'http://upload-service:8002',
    changeOrigin: true,
    pathRewrite: { '^/upload': '' },
    onError: proxyErrorHandler,
  })
);

// Route: /metadata/* -> http://metadata-service:8003
app.use(
  '/metadata',
  createProxyMiddleware({
    target: 'http://metadata-service:8003',
    changeOrigin: true,
    pathRewrite: { '^/metadata': '' },
    onError: proxyErrorHandler,
  })
);

// Fallback root route
app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

// Generic error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});

