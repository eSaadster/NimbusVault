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

// Middleware setup
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

// Metrics middleware
app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer({ method: req.method, route: req.path });
  res.on('finish', () => {
    end({ code: res.statusCode });
  });
  next();
});

// Rate Limiting
const authLimiter = rateLimit({ 
  windowMs: 60 * 1000, 
  max: 30,
  message: { error: 'Too many authentication attempts, please try again later' }
});
app.use('/api/auth', authLimiter);

// JWT Auth Middleware
function authMiddleware(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    logger.warn('Missing bearer token', { requestId: req.requestId, ip: req.ip });
    return res.status(401).json({ error: 'Missing bearer token' });
  }
  
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, SECRET);
    req.user = decoded;
    logger.debug('Token verified successfully', { 
      requestId: req.requestId, 
      userId: decoded.sub || decoded.id 
    });
    next();
  } catch (err) {
    logger.warn('Invalid token provided', { 
      requestId: req.requestId, 
      error: err.message,
      ip: req.ip 
    });
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// Proxy Helper with enhanced logging
const proxy = (path, target, requireAuth = true) => {
  const middlewares = [];
  
  if (requireAuth) middlewares.push(authMiddleware);
  
  middlewares.push(
    createProxyMiddleware({
      target,
      changeOrigin: true,
      pathRewrite: (pathReq) => pathReq.replace(new RegExp(`^${path}`), ''),
      onError: (err, req, res) => {
        logger.error('Proxy error', {
          requestId: req.requestId,
          target,
          path: req.path,
          error: err.message
        });
        res.status(502).json({ error: 'Bad gateway' });
      },
      onProxyReq: (proxyReq, req) => {
        logger.debug('Proxying request', {
          requestId: req.requestId,
          target,
          originalPath: req.path,
          method: req.method
        });
      },
      onProxyRes: (proxyRes, req) => {
        logger.debug('Proxy response received', {
          requestId: req.requestId,
          target,
          statusCode: proxyRes.statusCode
        });
      },
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
  logger.info('Health check endpoint accessed', { requestId: req.requestId });
  res.json({ 
    service: 'gateway',
    status: 'ok',
    timestamp: new Date().toISOString()
  });
});

// Health Endpoints
app.get('/health/live', (req, res) => {
  logger.debug('Liveness check', { requestId: req.requestId });
  res.json({ status: 'ok' });
});

app.get('/health/ready', (req, res) => {
  logger.debug('Readiness check', { requestId: req.requestId });
  res.json({ status: 'ok' });
});

app.get('/health/detailed', async (req, res) => {
  logger.info('Detailed health check initiated', { requestId: req.requestId });
  
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
      const responseTime = Date.now() - start;
      const status = resp.ok ? 'ok' : 'error';
      
      results[name] = { status, responseTime };
      
      logger.debug('Service health check completed', {
        requestId: req.requestId,
        service: name,
        status,
        responseTime
      });
    } catch (e) {
      const responseTime = Date.now() - start;
      results[name] = { status: 'error', responseTime };
      
      logger.warn('Service health check failed', {
        requestId: req.requestId,
        service: name,
        error: e.message,
        responseTime
      });
    }
  }
  
  const allOk = Object.values(results).every(r => r.status === 'ok');
  const overallStatus = allOk ? 'ok' : 'error';
  
  logger.info('Detailed health check completed', {
    requestId: req.requestId,
    overallStatus,
    serviceCount: Object.keys(services).length,
    healthyServices: Object.values(results).filter(r => r.status === 'ok').length
  });
  
  res.status(allOk ? 200 : 503).json({ 
    status: overallStatus, 
    services: results 
  });
});

app.get('/health/status', async (req, res) => {
  const start = Date.now();
  try {
    const response = await fetch(`http://localhost:${PORT}/health/detailed`).then(r => r.json());
    const totalTime = Date.now() - start;
    
    logger.info('Health status aggregation completed', {
      requestId: req.requestId,
      totalTime,
      status: response.status
    });
    
    res.status(response.status === 'ok' ? 200 : 503).json({ 
      ...response, 
      totalTime 
    });
  } catch (error) {
    logger.error('Health status aggregation failed', {
      requestId: req.requestId,
      error: error.message
    });
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  logger.debug('Metrics endpoint accessed', { requestId: req.requestId });
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// 404 handler
app.use((req, res) => {
  logger.warn('Route not found', {
    requestId: req.requestId,
    method: req.method,
    path: req.path,
    ip: req.ip
  });
  res.status(404).json({ error: 'Not Found' });
});

// Global error handler
app.use((err, req, res, _next) => {
  const requestId = req.requestId || uuidv4();
  logger.error('Unhandled error occurred', {
    requestId,
    error: err.message,
    stack: err.stack,
    method: req.method,
    path: req.path,
    ip: req.ip
  });
  res.status(500).json({ error: 'Internal Server Error' });
});

// Start server
app.listen(PORT, () => {
  logger.info('Gateway service started successfully', {
    port: PORT,
    nodeEnv: process.env.NODE_ENV || 'development',
    logLevel: process.env.LOG_LEVEL || 'info'
  });
});