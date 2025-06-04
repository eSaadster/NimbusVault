const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/health', (req, res) => {
  res.send('OK');
});

app.use(
  '/api/auth',
  createProxyMiddleware({
    target: 'http://auth-service:8001',
    changeOrigin: true,
    pathRewrite: { '^/api/auth': '' }
  })
);

app.use(
  '/api/upload',
  createProxyMiddleware({
    target: 'http://upload-service:8002',
    changeOrigin: true,
    pathRewrite: { '^/api/upload': '' }
  })
);

app.use(
  '/api/storage',
  createProxyMiddleware({
    target: 'http://storage-service:8003',
    changeOrigin: true,
    pathRewrite: { '^/api/storage': '' }
  })
);

app.use(
  '/api/metadata',
  createProxyMiddleware({
    target: 'http://metadata-service:8004',
    changeOrigin: true,
    pathRewrite: { '^/api/metadata': '' }
  })
);

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
