const express = require('express');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

function generateSignature(meetingNumber, role) {
  const iat = Math.floor(Date.now() / 1000) - 30;
  const exp = iat + 7200;

  const payload = {
    sdkKey: process.env.ZOOM_CLIENT_ID,
    appKey: process.env.ZOOM_CLIENT_ID,
    mn: meetingNumber,
    role: role,
    iat: iat,
    exp: exp,
    tokenExp: exp,
  };

  return jwt.sign(payload, process.env.ZOOM_CLIENT_SECRET, { algorithm: 'HS256' });
}

app.post('/api/signature', (req, res) => {
  const { meetingNumber, role } = req.body;

  if (meetingNumber === undefined || meetingNumber === null || meetingNumber === '') {
    return res.status(400).json({ error: 'meetingNumber は必須です' });
  }

  if (role === undefined || role === null) {
    return res.status(400).json({ error: 'role は必須です' });
  }

  const signature = generateSignature(meetingNumber, role);
  res.json({ signature });
});

const PORT = process.env.PORT || 3000;

// テスト時は PORT=0（supertest が直接 app を使う）、
// 通常起動時は 3000 でリッスンする
if (process.env.PORT !== '0') {
  app.listen(PORT, () => {
    console.log(`サーバーが起動しました: http://localhost:${PORT}`);
  });
}

module.exports = { app, generateSignature };
