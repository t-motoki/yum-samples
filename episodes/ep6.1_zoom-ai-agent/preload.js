// contextIsolation: false + nodeIntegration: true のため
// renderer.js は直接 process.env にアクセスできる。
// preload は dotenv の読み込みだけ担当する。
require('dotenv').config({ path: require('path').join(__dirname, '.env') });
