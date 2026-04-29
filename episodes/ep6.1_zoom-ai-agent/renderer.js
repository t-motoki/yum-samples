const { ZoomMtg } = require('@zoom/meetingsdk');
const { askGemini } = require('./gemini');

console.log('[bot] GEMINI_API_KEY loaded:', !!process.env.GEMINI_API_KEY);
ZoomMtg.preLoadWasm();

function addLog(message, type = 'info') {
  const log = document.getElementById('log');
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const time = new Date().toLocaleTimeString('ja-JP');
  entry.textContent = `[${time}] ${message}`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

async function getSignature(meetingNumber, role) {
  const response = await fetch('http://localhost:3000/api/signature', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meetingNumber, role }),
  });

  if (!response.ok) {
    throw new Error(`署名の取得に失敗しました: ${response.status}`);
  }

  const data = await response.json();
  return data.signature;
}

async function handleBotMessage(prompt, senderName) {
  addLog(`「${senderName}」からの質問: ${prompt}`, 'receive');

  try {
    const response = await askGemini(prompt);
    console.log('[bot] Gemini response:', response);

    const message = `@${senderName} ${response}`;
    console.log('[bot] sendChat message:', message);

    ZoomMtg.sendChat({
      message,
      success: (res) => console.log('[bot] sendChat success:', res),
      error: (err) => console.log('[bot] sendChat error:', JSON.stringify(err)),
    });
  } catch (err) {
    console.log('[bot] error:', err.message, err.stack);
  }
}

async function joinMeeting() {
  const meetingNumber = document.getElementById('meeting-number').value.replace(/\s/g, '');
  const password = document.getElementById('password').value;
  const displayName = document.getElementById('display-name').value || 'AI Agent';

  if (!meetingNumber) {
    addLog('ミーティング番号を入力してください', 'error');
    return;
  }

  document.getElementById('join-btn').disabled = true;
  addLog('署名を取得中...', 'info');

  let signature;
  try {
    signature = await getSignature(meetingNumber, 0);
  } catch (err) {
    addLog(`エラー: ${err.message}`, 'error');
    document.getElementById('join-btn').disabled = false;
    return;
  }

  addLog('Zoom SDK を初期化中...', 'info');
  ZoomMtg.prepareWebSDK();

  ZoomMtg.init({
    leaveUrl: 'http://localhost:3000/left',
    patchJsMedia: true,
    success: () => {
      addLog('SDK 初期化完了。ミーティングに参加中...', 'info');
      console.log('[bot] init success');

      registerChatListener();

      ZoomMtg.inMeetingServiceListener('onMeetingStatus', (data) => {
        console.log('[bot] onMeetingStatus:', data);
        addLog(`ミーティング状態: ${JSON.stringify(data)}`, 'info');
      });

      ZoomMtg.join({
        meetingNumber: meetingNumber,
        userName: displayName,
        signature: signature,
        sdkKey: process.env.ZOOM_CLIENT_ID,
        passWord: password,
        success: (res) => {
          console.log('[bot] join success:', res);
          addLog('ミーティングに参加しました', 'info');
        },
        error: (err) => {
          console.log('[bot] join error:', err);
          addLog(`参加エラー: ${JSON.stringify(err)}`, 'error');
          document.getElementById('join-btn').disabled = false;
        },
      });
    },
    error: (err) => {
      addLog(`初期化エラー: ${JSON.stringify(err)}`, 'error');
      document.getElementById('join-btn').disabled = false;
    },
  });
}

function registerChatListener() {
  console.log('[bot] registerChatListener called');
  ZoomMtg.inMeetingServiceListener('onReceiveChatMsg', (data) => {
    const message = data.content?.text;
    const senderName = data.sender;
    console.log('[bot] chat received:', senderName, message);
    addLog(`受信: [${senderName}] ${message}`, 'receive');

    if (message?.startsWith('@bot')) {
      const prompt = message.replace('@bot', '').trim();
      console.log('[bot] calling Gemini with:', prompt);
      handleBotMessage(prompt, senderName);
    }
  });

  addLog('チャット受信リスナーを登録しました', 'info');
}
