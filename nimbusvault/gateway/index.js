const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

// Basic health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'gateway',
    timestamp: new Date().toISOString(),
  });
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
