function createLogger(serviceName) {
  function log(level, message) {
    const entry = {
      timestamp: new Date().toISOString(),
      service: serviceName,
      level: level,
      message: message
    };
    console.log(JSON.stringify(entry));
  }

  return {
    info: (msg) => log('INFO', msg),
    error: (msg) => log('ERROR', msg),
    warn: (msg) => log('WARN', msg),
    debug: (msg) => log('DEBUG', msg)
  };
}

module.exports = { createLogger };
