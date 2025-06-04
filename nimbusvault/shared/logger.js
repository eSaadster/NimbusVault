const { createLogger, format, transports } = require('winston');
const { v4: uuidv4 } = require('uuid');

function buildLogger(service) {
  return createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: format.combine(
      format.timestamp(),
      format.printf(({ timestamp, level, message, requestId }) => {
        return JSON.stringify({
          timestamp,
          service,
          level: level.toUpperCase(),
          message,
          request_id: requestId,
        });
      })
    ),
    transports: [new transports.Console()],
  });
}

function requestMiddleware(logger) {
  return function (req, res, next) {
    let requestId = req.headers['x-request-id'];
    if (!requestId) {
      requestId = uuidv4().replace(/-/g, '');
    }
    req.requestId = requestId;
    res.setHeader('X-Request-ID', requestId);
    logger.info(`Incoming ${req.method} ${req.url}`, { requestId });
    res.on('finish', () => {
      logger.info(`Response ${res.statusCode} ${req.method} ${req.url}`, { requestId });
    });
    next();
  };
}

module.exports = { buildLogger, requestMiddleware };
