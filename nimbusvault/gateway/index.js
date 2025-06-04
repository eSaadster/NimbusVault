const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.AUTH_SECRET || 'secret';

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

// Proxies
app.use('/upload', authMiddleware, createProxyMiddleware({
  target: 'http://upload-service:8002',
  changeOrigin: true,
  pathRewrite: {
    '^/upload': '',
  },
}));

app.use('/metadata', authMiddleware, createProxyMiddleware({
  target: 'http://metadata-service:8003',
  changeOrigin: true,
  pathRewrite: {
    '^/metadata': '',
  },
}));

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
