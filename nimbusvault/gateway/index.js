const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const helmet = require('helmet');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const jwt = require('jsonwebtoken');
const http = require('http');
const { buildLogger, requestMiddleware } = require('../shared/logger');

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.AUTH_SECRET || 'secret';
const logger = buildLogger('gateway');

// Basic Middleware
app.use(express.json());
app.use(cookieParser());
app.use(helmet());
app.use(cors({ origin: 'http://localhost:3001', credentials: true }));

// Logging & Request ID Middleware
app.use(requestMiddleware(logger));

// Rate Limiting for auth routes
const authLimiter = rateLimit({ windowMs: 60 * 1000, max: 30 });
app.use('/api/auth', authLimiter);

// JWT Authentication Middleware
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
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// Proxy helper
const proxy = (path, target, requireAuth = true) => {
  const middlewares = [];
  if (requireAuth) middlewares.push(authMiddleware);
  middlewares.push(
    createProxyMiddleware({
      target,
      changeOrigin: true,
      pathRewrite: (pathReq) => pathReq.replace(new RegExp(`^${path}`), ''),
      onError: (_err, _req, res) => res.status(502).json({ error: 'Bad gateway' }),
      logLevel: 'warn',
    })
  );
  return middlewares;
};

// Route proxies
app.use('/api/auth', ...proxy('/api/auth', 'http://auth-service:8001', false));
app.use('/api/upload', ...proxy('/api/upload', 'http://upload-service:8002'));
app.use('/api/metadata', ...proxy('/api/metadata', 'http://metadata-service:8003'));
app.use('/api/storage', ...proxy('/api/storage', 'http://storage-service:8004'));

// Health Check
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

// Root
app.get('/', (req, res) => {
  logger.info('Health check', { requestId: req.requestId });
  res.send('Hello from gateway');
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found' });
});

// Global error handler
app.use((err, req, res, _next) => {
  logger.error(`Unhandled error: ${err}`, { requestId: req.requestId });
  res.status(500).json({ error: 'Internal Server Error' });
});

// Start server
app.listen(PORT, () => {
  logger.info(`Gateway running on port ${PORT}`);
});
