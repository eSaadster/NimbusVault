const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const http = require('http');

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.AUTH_SECRET || 'secret';

// Enable CORS
app.use(cors());

// Simple request logger
app.use((req, res, next) => {
  console.log(`${req.method} ${req.originalUrl}`);
  next();
});

// Additional manual CORS headers (defensive)
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

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

// Proxy helper with error handler
const proxy = (path, target, requireAuth = true) => {
  const middlewares = [];
  if (requireAuth) middlewares.push(authMiddleware);
  middlewares.push(
    createProxyMiddleware({
      target,
      changeOrigin: true,
      pathRewrite: (pathReq) => pathReq.replace(new RegExp(`^${path}`), ''),
      onError: (_err, _req, res) => {
        res.status(502).json({ error: 'Bad gateway' });
      },
      logLevel: 'warn',
    })
  );
  return middlewares;
};

// Auth proxy (no auth middleware)
app.use('/api/auth', ...proxy('/api/auth', 'http://auth-service:8001', false));

// Protected routes
app.use('/api/upload', ...proxy('/api/upload', 'http://upload-service:8002'));
app.use('/api/metadata', ...proxy('/api/metadata', 'http://metadata-service:8003'));
app.use('/api/storage', ...proxy('/api/storage', 'http://storage-service:8004'));

// Health check for all services
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

// Root route
app.get('/', (_req, res) => {
  res.send('Hello from gateway');
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found' });
});

// General error handler
app.use((err, req, res, _next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
