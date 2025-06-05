const express = require('express');
const logger = require('../shared/logger');
const app = express();
const PORT = process.env.PORT || 3000;

app.use((req, res, next) => {
  logger.info(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.listen(PORT, () => {
  logger.info(`Gateway running on port ${PORT}`);
});
