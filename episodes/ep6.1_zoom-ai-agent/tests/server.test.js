/**
 * server.js のテスト
 * JWT 生成ロジックと /api/signature エンドポイントを検証する
 */

const jwt = require('jsonwebtoken');
const request = require('supertest');

// テスト用の環境変数を設定する（本物の鍵は不要）
process.env.ZOOM_CLIENT_ID = 'test_client_id';
process.env.ZOOM_CLIENT_SECRET = 'test_client_secret';
process.env.PORT = '0'; // ランダムポートでテスト

const { app, generateSignature } = require('../server');

describe('generateSignature', () => {
  test('HS256 で署名された JWT を返す', () => {
    const meetingNumber = '123456789';
    const role = 0;

    const signature = generateSignature(meetingNumber, role);

    // 署名を検証できること
    const decoded = jwt.verify(signature, 'test_client_secret', { algorithms: ['HS256'] });

    expect(decoded.sdkKey).toBe('test_client_id');
    expect(decoded.appKey).toBe('test_client_id');
    expect(decoded.mn).toBe(meetingNumber);
    expect(decoded.role).toBe(role);
  });

  test('iat は現在時刻より 30 秒前', () => {
    const now = Math.floor(Date.now() / 1000);
    const signature = generateSignature('123456789', 0);
    const decoded = jwt.decode(signature);

    // 30秒前 ±5秒の許容範囲
    expect(decoded.iat).toBeGreaterThanOrEqual(now - 35);
    expect(decoded.iat).toBeLessThanOrEqual(now - 25);
  });

  test('exp は iat から 2 時間後', () => {
    const signature = generateSignature('123456789', 0);
    const decoded = jwt.decode(signature);

    expect(decoded.exp).toBe(decoded.iat + 7200);
    expect(decoded.tokenExp).toBe(decoded.iat + 7200);
  });
});

describe('POST /api/signature', () => {
  test('有効なリクエストで 200 と signature を返す', async () => {
    const response = await request(app)
      .post('/api/signature')
      .send({ meetingNumber: '123456789', role: 0 })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('signature');
    expect(typeof response.body.signature).toBe('string');
  });

  test('meetingNumber が未指定のとき 400 を返す', async () => {
    const response = await request(app)
      .post('/api/signature')
      .send({ role: 0 })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
  });

  test('role が未指定のとき 400 を返す', async () => {
    const response = await request(app)
      .post('/api/signature')
      .send({ meetingNumber: '123456789' })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
  });
});
