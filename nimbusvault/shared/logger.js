const { createLogger: winstonCreateLogger, format, transports } = require('winston');
const { v4: uuidv4 } = require('uuid');

/**
 * Simple legacy logger (backward compatibility)
 * This maintains compatibility with existing code that expects a simple logger
 */
const logger = {
  info: (message) => {
    console.log(message);
  },
  error: (message) => {
    console.error(message);
  },
  warn: (message) => {
    console.warn(message);
  },
  debug: (message) => {
    console.debug(message);
  }
};

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

/**
 * Create a simple console logger for quick debugging
 * @param {string} prefix - Optional prefix for log messages
 * @returns {Object} Simple logger interface
 */
function createSimpleLogger(prefix = '') {
  const logPrefix = prefix ? `[${prefix}] ` : '';
  
  return {
    info: (message) => console.log(`${logPrefix}${message}`),
    error: (message) => console.error(`${logPrefix}${message}`),
    warn: (message) => console.warn(`${logPrefix}${message}`),
    debug: (message) => console.debug(`${logPrefix}${message}`)
  };
}

/**
 * Auto-detect and create appropriate logger based on environment
 * @param {string} serviceName - Name of the service
 * @param {Object} options - Configuration options
 * @returns {Object} Appropriate logger for the environment
 */
function autoLogger(serviceName, options = {}) {
  // Use simple logger in test environment or when Winston is not available
  try {
    if (process.env.NODE_ENV === 'test' || options.simple) {
      return createLogger(serviceName);
    }
    return buildLogger(serviceName, options);
  } catch (error) {
    console.warn('Winston logger creation failed, falling back to simple logger:', error.message);
    return createLogger(serviceName);
  }
}

module.exports = {
  // Legacy exports for backward compatibility
  logger,
  
  // Factory functions
  createLogger,
  buildLogger,
  createSimpleLogger,
  autoLogger,
  
  // Middleware and utilities
  requestMiddleware,
  createChildLogger,
  getRequestLogger
};