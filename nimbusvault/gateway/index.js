const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.use('/api/auth', createProxyMiddleware({
  target: 'http://auth-service:8001',
  changeOrigin: true,
  pathRewrite: { '^/api/auth': '' },
}));

app.use('/api/upload', createProxyMiddleware({
  target: 'http://upload-service:8002',
  changeOrigin: true,
  pathRewrite: { '^/api/upload': '' },
}));

app.use('/api/metadata', createProxyMiddleware({
  target: 'http://metadata-service:8003',
  changeOrigin: true,
  pathRewrite: { '^/api/metadata': '' },
}));

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
