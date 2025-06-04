const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const helmet = require('helmet');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const fetch = require('node-fetch');
const { buildLogger, requestMiddleware } = require('../shared/logger');

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.AUTH_SECRET || 'secret';
const logger = buildLogger('gateway');

// Middleware Setup
app.use(express.json());
app.use(cookieParser());
app.use(helmet());
app.use(cors({ origin: 'http://localhost:3001', credentials: true }));
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

// Health Check Endpoint
const services = {
  auth: process.env.AUTH_SERVICE_URL || 'http://auth-service:8001/health',
  upload: process.env.UPLOAD_SERVICE_URL || 'http://upload-service:8002/health',
  metadata: process.env.METADATA_SERVICE_URL || 'http://metadata-service:8003/health',
  storage: process.env.STORAGE_SERVICE_URL || 'http://storage-service:8004/health',
};

app.get('/health', async (_req, res) => {
  const results = {};

  await Promise.all(
    Object.entries(services).map(async ([name, url]) => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2000);
      try {
        const response = await fetch(url, { signal: controller.signal });
        results[name] = response.ok ? 'healthy' : 'unhealthy';
      } catch (err) {
        results[name] = 'unhealthy';
      } finally {
        clearTimeout(timeout);
      }
    })
  );

  const overall = Object.values(results).every((s) => s === 'healthy')
    ? 'healthy'
    : 'unhealthy';

  res.json({ status: overall, services: results });
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
  logger.error(`Unhandled error: ${err}`, { requestId: req.requestId || uuidv4() });
  res.status(500).json({ error: 'Internal Server Error' });
});

// Start server
app.listen(PORT, () => {
  logger.info(`Gateway running on port ${PORT}`);
});