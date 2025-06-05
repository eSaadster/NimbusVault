const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Hello from gateway');
});

app.listen(PORT, () => {
  console.log(`Gateway running on port ${PORT}`);
});
