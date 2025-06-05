const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const fetch = require('node-fetch');
const client = require('prom-client');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { buildLogger, requestMiddleware } = require('../shared/logger');

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.AUTH_SECRET || 'secret';
const logger = buildLogger('gateway');

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(helmet());
app.use(cors({ origin: 'http://localhost:3001', credentials: true }));
app.use(requestMiddleware(logger));

// Prometheus Metrics
const register = new client.Registry();
client.collectDefaultMetrics({ register });
const httpRequestDuration = new client.Histogram({
  name: 'gateway_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'code'],
});
register.registerMetric(httpRequestDuration);

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer({ method: req.method, route: req.path });
  res.on('finish', () => {
    end({ code: res.statusCode });
  });
  next();
});

// Rate Limiting
const authLimiter = rateLimit({ windowMs: 60 * 1000, max: 30 });
app.use('/api/auth', authLimiter);

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
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// Proxy Helper
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

// Route Proxies
app.use('/api/auth', ...proxy('/api/auth', 'http://auth-service:8001', false));
app.use('/api/upload', ...proxy('/api/upload', 'http://upload-service:8002'));
app.use('/api/metadata', ...proxy('/api/metadata', 'http://metadata-service:8003'));
app.use('/api/storage', ...proxy('/api/storage', 'http://storage-service:8004'));

// Root route
app.get('/', (req, res) => {
  logger.info('Health check', { requestId: req.requestId });
  res.send('Hello from gateway');
});

// Health Endpoints
app.get('/health/live', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/health/ready', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/health/detailed', async (req, res) => {
  const services = {
    'auth-service': 'http://auth-service:8001/health/ready',
    'upload-service': 'http://upload-service:8002/health/ready',
    'metadata-service': 'http://metadata-service:8003/health/ready',
    'admin-ui': 'http://admin-ui:3001/api/health/ready',
  };
  const results = {};
  for (const [name, url] of Object.entries(services)) {
    const start = Date.now();
    try {
      const resp = await fetch(url, { timeout: 500 });
      results[name] = { status: resp.ok ? 'ok' : 'error', responseTime: Date.now() - start };
    } catch (e) {
      results[name] = { status: 'error', responseTime: Date.now() - start };
    }
  }
  const allOk = Object.values(results).every(r => r.status === 'ok');
  res.status(allOk ? 200 : 503).json({ status: allOk ? 'ok' : 'error', services: results });
});

app.get('/health/status', async (req, res) => {
  const start = Date.now();
  const response = await fetch(`http://localhost:${PORT}/health/detailed`).then(r => r.json());
  const totalTime = Date.now() - start;
  res.status(response.status === 'ok' ? 200 : 503).json({ ...response, totalTime });
});

// Metrics endpoint
app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
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
