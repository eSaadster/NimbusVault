const { createLogger: winstonCreateLogger, format, transports } = require('winston');
const { v4: uuidv4 } = require('uuid');

/**
 * Simple logger factory (legacy interface)
 * @param {string} serviceName - Name of the service
 * @returns {Object} Logger with info, error, warn, debug methods
 */
function createLogger(serviceName) {
  function log(level, message, meta = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      service: serviceName,
      level: level,
      message: message,
      ...meta
    };
    console.log(JSON.stringify(entry));
  }

  return {
    info: (msg, meta) => log('INFO', msg, meta),
    error: (msg, meta) => log('ERROR', msg, meta),
    warn: (msg, meta) => log('WARN', msg, meta),
    debug: (msg, meta) => log('DEBUG', msg, meta)
  };
}

/**
 * Advanced logger factory using Winston
 * @param {string} service - Name of the service
 * @param {Object} options - Configuration options
 * @returns {winston.Logger} Configured Winston logger
 */
function buildLogger(service, options = {}) {
  const {
    level = process.env.LOG_LEVEL || 'info',
    enableConsole = true,
    enableFile = false,
    filename = 'app.log'
  } = options;

  const logTransports = [];
  
  if (enableConsole) {
    logTransports.push(new transports.Console());
  }
  
  if (enableFile) {
    logTransports.push(new transports.File({ filename }));
  }

  return winstonCreateLogger({
    level,
    format: format.combine(
      format.timestamp(),
      format.errors({ stack: true }),
      format.printf(({ timestamp, level, message, requestId, stack, ...meta }) => {
        const logEntry = {
          timestamp,
          service,
          level: level.toUpperCase(),
          message,
          ...(requestId && { request_id: requestId }),
          ...(stack && { stack }),
          ...(Object.keys(meta).length > 0 && { meta })
        };
        return JSON.stringify(logEntry);
      })
    ),
    transports: logTransports,
  });
}

/**
 * Express middleware for request logging and ID tracking
 * @param {winston.Logger} logger - Winston logger instance
 * @param {Object} options - Middleware options
 * @returns {Function} Express middleware function
 */
function requestMiddleware(logger, options = {}) {
  const {
    logRequests = true,
    logResponses = true,
    generateId = true
  } = options;

  return function (req, res, next) {
    let requestId = req.headers['x-request-id'];
    
    if (!requestId && generateId) {
      requestId = uuidv4().replace(/-/g, '');
    }
    
    if (requestId) {
      req.requestId = requestId;
      res.setHeader('X-Request-ID', requestId);
    }

    if (logRequests) {
      logger.info(`Incoming ${req.method} ${req.url}`, { requestId });
    }

    if (logResponses) {
      res.on('finish', () => {
        logger.info(`Response ${res.statusCode} ${req.method} ${req.url}`, { requestId });
      });
    }

    next();
  };
}

/**
 * Create a child logger with additional context
 * @param {winston.Logger} parentLogger - Parent logger instance
 * @param {Object} context - Additional context to include in logs
 * @returns {Object} Child logger with context
 */
function createChildLogger(parentLogger, context = {}) {
  return {
    info: (message, meta = {}) => parentLogger.info(message, { ...context, ...meta }),
    error: (message, meta = {}) => parentLogger.error(message, { ...context, ...meta }),
    warn: (message, meta = {}) => parentLogger.warn(message, { ...context, ...meta }),
    debug: (message, meta = {}) => parentLogger.debug(message, { ...context, ...meta })
  };
}

/**
 * Get logger with request context
 * @param {winston.Logger} logger - Base logger
 * @param {Object} req - Express request object
 * @returns {Object} Logger with request context
 */
function getRequestLogger(logger, req) {
  const context = {};
  if (req.requestId) {
    context.requestId = req.requestId;
  }
  return createChildLogger(logger, context);
}

module.exports = {
  createLogger,
  buildLogger,
  requestMiddleware,
  createChildLogger,
  getRequestLogger
};