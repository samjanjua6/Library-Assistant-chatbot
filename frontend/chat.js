'use strict';

// ── auth guard ─────────────────────────────────────────────────────────────
const token    = localStorage.getItem('zylo_token');
const username = localStorage.getItem('zylo_username') || 'You';

if (!token) {
  // No token → send to login
  window.location.replace('/');
}

// ── DOM refs ───────────────────────────────────────────────────────────────
const messagesEl       = document.getElementById('chat-messages');
const chatForm         = document.getElementById('chat-form');
const chatInput        = document.getElementById('chat-input');
const chatSend         = document.getElementById('chat-send');
const wsDot            = document.getElementById('ws-status-dot');
const wsLabel          = document.getElementById('ws-status-label');
const usernameDisplay  = document.getElementById('username-display');
const userAvatar       = document.getElementById('user-avatar');
const logoutBtn        = document.getElementById('logout-btn');

// ── populate user info ─────────────────────────────────────────────────────
usernameDisplay.textContent = username;
userAvatar.textContent = username.charAt(0).toUpperCase();

// ── logout ─────────────────────────────────────────────────────────────────
logoutBtn.addEventListener('click', () => {
  localStorage.removeItem('zylo_token');
  localStorage.removeItem('zylo_username');
  window.location.replace('/');
});

// ── message rendering ──────────────────────────────────────────────────────
function removeIntro() {
  const intro = document.getElementById('chat-intro');
  if (intro) intro.remove();
}

function addMessage(text, type = 'system') {
  removeIntro();

  const row = document.createElement('div');
  row.className = `msg msg--${type}`;

  if (type !== 'system') {
    const av = document.createElement('div');
    av.className = 'msg-avatar';
    av.setAttribute('aria-hidden', 'true');
    av.textContent = type === 'user' ? username.charAt(0).toUpperCase() : '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    if (type === 'user') {
      row.appendChild(bubble);
      row.appendChild(av);
    } else {
      row.appendChild(av);
      row.appendChild(bubble);
    }
  } else {
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;
    row.appendChild(bubble);
  }

  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ── WebSocket connection ───────────────────────────────────────────────────
let ws = null;

function setStatus(state) {
  wsDot.className = 'ws-dot';
  switch (state) {
    case 'online':
      wsDot.classList.add('ws-dot--online');
      wsLabel.textContent = 'Connected';
      chatInput.disabled = false;
      chatSend.disabled = false;
      chatInput.focus();
      break;
    case 'connecting':
      wsDot.classList.add('ws-dot--connecting');
      wsLabel.textContent = 'Connecting…';
      chatInput.disabled = true;
      chatSend.disabled = true;
      break;
    default:
      wsDot.classList.add('ws-dot--offline');
      wsLabel.textContent = 'Disconnected';
      chatInput.disabled = true;
      chatSend.disabled = true;
  }
}

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url   = `${proto}//${location.host}/ws/chat?token=${encodeURIComponent(token)}`;

  setStatus('connecting');
  ws = new WebSocket(url);

  ws.onopen = () => {
    setStatus('online');
  };

  ws.onmessage = (e) => {
    addMessage(e.data, 'bot');
  };

  ws.onclose = (e) => {
    setStatus('offline');
    if (e.code === 1008) {
      // Policy violation = token invalid/expired
      addMessage('⚠ Session expired. Redirecting to login…', 'system');
      localStorage.removeItem('zylo_token');
      localStorage.removeItem('zylo_username');
      setTimeout(() => window.location.replace('/'), 1800);
    } else if (e.code !== 1000) {
      // Unexpected close → retry
      addMessage('Connection lost. Reconnecting in 3 s…', 'system');
      setTimeout(connect, 3000);
    }
  };

  ws.onerror = () => {
    addMessage('WebSocket error. Check the backend.', 'system');
  };
}

// ── send message ───────────────────────────────────────────────────────────
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    addMessage('Not connected yet — please wait.', 'system');
    return;
  }
  addMessage(text, 'user');
  ws.send(text);
  chatInput.value = '';
  chatInput.focus();
});

// ── start ──────────────────────────────────────────────────────────────────
setStatus('offline');
connect();
