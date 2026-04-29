require('dotenv').config();
const { app, BrowserWindow } = require('electron');
const path = require('path');

app.commandLine.appendSwitch('enable-unsafe-swiftshader');
app.commandLine.appendSwitch('no-sandbox');
app.commandLine.appendSwitch('disable-gpu-sandbox');
app.commandLine.appendSwitch('disable-dev-shm-usage');

// ローカル Express サーバーを起動する
require('./server');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: false,
      // renderer.js が require('@zoom/meetingsdk') を使うため有効にする
      nodeIntegration: true,
      // Zoom SDK が WebAssembly を使うため webSecurity を無効にする
      webSecurity: false,
    },
  });

  win.loadFile('index.html');
  win.webContents.on('console-message', (event, level, message) => {
    console.log('[renderer]', message);
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
