const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const path = require('path');
const authMiddleware = require('../shared/auth_middleware');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(cookieParser());
app.use(cors({ origin: 'http://localhost:3001', credentials: true }));
app.use(helmet());

const authLimiter = rateLimit({ windowMs: 60 * 1000, max: 30 });
app.use('/auth', authLimiter);

app.get('/public', (req, res) => {
  res.send('Public route');
});

app.get('/protected', authMiddleware, (req, res) => {
  res.json({ message: 'Protected route', user: req.user });
});

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});

