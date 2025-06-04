const express = require('express');
const { buildLogger, requestMiddleware } = require('../shared/logger');

const app = express();
const PORT = process.env.PORT || 3000;
const logger = buildLogger('gateway');

app.use(requestMiddleware(logger));

app.get('/', (req, res) => {
  logger.info('Health check', { requestId: req.requestId });
  res.send('Hello from gateway');
});

app.use((err, req, res, next) => {
  logger.error(`Unhandled error: ${err}`, { requestId: req.requestId });
  res.status(500).json({ detail: 'Internal Server Error' });
});

app.listen(PORT, () => {
  logger.info(`Gateway running on port ${PORT}`);
});
