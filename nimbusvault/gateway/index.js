const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.AUTH_SECRET || 'secret';

// Enable CORS for all routes
app.use(cors());

// JWT Auth Middleware
function authMiddleware(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing bearer token' });
  }
  const token = authHeader.split(' ')[1];
  try {
    jwt.verify(token, SECRET);
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Common error handler for proxy failures
const proxyErrorHandler = (err, req, res) => {
  console.error('Proxy error:', err);
  if (!res.headersSent) {
    res.status(500).json({ error: 'Proxy error' });
  }
};

// Proxy routes
app.use(
  '/auth',
  createProxyMiddleware({
    target: 'http://auth-service:8001',
    changeOrigin: true,
    pathRewrite: { '^/auth': '' },
    onError: proxyErrorHandler,
  })
);

app.use(
  '/upload',
  authMiddleware,
  createProxyMiddleware({
    target: 'http://upload-service:8002',
    changeOrigin: true,
    pathRewrite: { '^/upload': '' },
    onError: proxyErrorHandler,
  })
);

app.use(
  '/metadata',
  authMiddleware,
  createProxyMiddleware({
    target: 'http://metadata-service:8003',
    changeOrigin: true,
    pathRewrite: { '^/metadata': '' },
    onError: proxyErrorHandler,
  })
);

app.use(
  '/storage',
  authMiddleware,
  createProxyMiddleware({
    target: 'http://storage-service:8004',
    changeOrigin: true,
    pathRewrite: { '^/storage': '' },
    onError: proxyErrorHandler,
  })
);

// Health check route
app.get('/health', (req, res) => {
  res.json({ service: 'gateway', status: 'OK' });
});

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
