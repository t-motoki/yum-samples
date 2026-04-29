/**
 * gemini.js のテスト
 * モジュールのインターフェースと API 呼び出しの動作を検証する
 */

// Google Generative AI をモックする（実際の API を呼ばない）
jest.mock('@google/generative-ai', () => {
  return {
    GoogleGenerativeAI: jest.fn().mockImplementation(() => ({
      getGenerativeModel: jest.fn().mockReturnValue({
        generateContent: jest.fn().mockResolvedValue({
          response: {
            text: () => 'モックの応答テキスト',
          },
        }),
      }),
    })),
  };
});

process.env.GEMINI_API_KEY = 'test_api_key';

const { askGemini } = require('../gemini');

describe('askGemini', () => {
  test('文字列を返す', async () => {
    const result = await askGemini('テストプロンプト');
    expect(typeof result).toBe('string');
  });

  test('Gemini の応答テキストをそのまま返す', async () => {
    const result = await askGemini('テストプロンプト');
    expect(result).toBe('モックの応答テキスト');
  });

  test('空のプロンプトでもエラーを投げない', async () => {
    await expect(askGemini('')).resolves.toBeDefined();
  });
});
