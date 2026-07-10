const output = document.getElementById('output');
const clearButton = document.getElementById('clear-output');
const userPreview = document.getElementById('user-preview');

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

async function sendRequest(url, options) {
  const response = await fetch(url, options);
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

clearButton.addEventListener('click', () => {
  writeOutput('Use one of the forms above to test the API.');
  resetUserPreview();
});