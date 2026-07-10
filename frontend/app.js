const API_BASE_URL = window.location.origin;

const output = document.getElementById('output');
const clearButton = document.getElementById('clear-output');
const userPreview = document.getElementById('user-preview');
const chatLog = document.getElementById('chat-log');
const chatStatus = document.getElementById('chat-status');
const connectChatButton = document.getElementById('connect-chat');
const disconnectChatButton = document.getElementById('disconnect-chat');
const chatForm = document.getElementById('chat-form');

let chatSocket = null;

function writeOutput(value, isError = false) {
  output.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  output.style.color = isError ? '#fecdd3' : '#dbeafe';
}

function renderUserPreview(user) {
  userPreview.classList.remove('empty');
  userPreview.innerHTML = `
    <p class="user-title">${user.username}</p>
    <dl>
      <dt>ID</dt>
      <dd>${user.id}</dd>
      <dt>Email</dt>
      <dd>${user.email}</dd>
      <dt>Created At</dt>
      <dd>${user.created_at}</dd>
    </dl>
  `;
}

function resetUserPreview() {
  userPreview.classList.add('empty');
  userPreview.innerHTML = '<p>No user loaded yet. Enter a user id above and click <strong>Fetch user</strong>.</p>';
}

function addChatLine(text, type = 'system') {
  const item = document.createElement('div');
  item.className = `chat-message ${type}`;
  item.textContent = text;
  chatLog.appendChild(item);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setChatStatus(online, label) {
  chatStatus.textContent = label;
  chatStatus.classList.toggle('online', online);
  chatStatus.classList.toggle('offline', !online);
}

function connectChat() {
  if (chatSocket && (chatSocket.readyState === WebSocket.OPEN || chatSocket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  chatSocket = new WebSocket(`${protocol}//${window.location.host}/ws/chat`);

  setChatStatus(false, 'Connecting...');

  chatSocket.onopen = () => {
    setChatStatus(true, 'Connected');
    addChatLine('Connected to the AI bot.', 'system');
  };

  chatSocket.onmessage = (event) => {
    addChatLine(event.data, 'bot');
  };

  chatSocket.onclose = () => {
    setChatStatus(false, 'Disconnected');
    addChatLine('Chat disconnected.', 'system');
  };

  chatSocket.onerror = () => {
    addChatLine('Chat error. Check the backend server.', 'system');
  };
}

function disconnectChat() {
  if (chatSocket) {
    chatSocket.close();
    chatSocket = null;
  }
}

async function sendRequest(url, options) {
  const response = await fetch(`${API_BASE_URL}${url}`, options);
  const text = await response.text();
  let parsed;

  try {
    parsed = text ? JSON.parse(text) : {};
  } catch {
    parsed = text;
  }

  if (!response.ok) {
    const message = typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
    throw new Error(`HTTP ${response.status}\n${message}`);
  }

  return parsed;
}

document.getElementById('signup-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await sendRequest('/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    writeOutput(data);
  } catch (error) {
    writeOutput(error.message, true);
  }
});

document.getElementById('login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await sendRequest('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    writeOutput(data);
  } catch (error) {
    writeOutput(error.message, true);
  }
});

document.getElementById('user-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const userId = formData.get('user_id');

  try {
    const data = await sendRequest(`/users/${userId}`);
    writeOutput(data);
    renderUserPreview(data);
  } catch (error) {
    writeOutput(error.message, true);
    resetUserPreview();
  }
});

connectChatButton.addEventListener('click', connectChat);
disconnectChatButton.addEventListener('click', disconnectChat);

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const message = String(formData.get('chat_message') || '').trim();

  if (!message) {
    return;
  }

  if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
    addChatLine('Connect to the chat first.', 'system');
    return;
  }

  addChatLine(message, 'user');
  chatSocket.send(message);
  event.currentTarget.reset();
});

clearButton.addEventListener('click', () => {
  writeOutput('Use one of the forms above to test the API.');
  resetUserPreview();
});

addChatLine('Click Connect to start a live chat.', 'system');
setChatStatus(false, 'Disconnected');