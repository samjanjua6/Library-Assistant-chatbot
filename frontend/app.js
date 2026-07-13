'use strict';

// ── helpers ────────────────────────────────────────────────────────────────
function $(id) { return document.getElementById(id); }

function showAlert(message, type = 'error') {
  const el = $('auth-alert');
  el.textContent = message;
  el.className = `auth-alert ${type}`;
  el.classList.remove('hidden');
}

function hideAlert() {
  $('auth-alert').className = 'auth-alert hidden';
}

function setLoading(btnId, loading) {
  const btn = $(btnId);
  btn.disabled = loading;
  btn.querySelector('.btn-text').classList.toggle('hidden', loading);
  btn.querySelector('.btn-spinner').classList.toggle('hidden', !loading);
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

// ── redirect if already authenticated ─────────────────────────────────────
if (localStorage.getItem('zylo_token')) {
  window.location.replace('/chat');
}

// ── tab switching ──────────────────────────────────────────────────────────
function showPanel(name) {
  hideAlert();
  const isLogin = name === 'login';

  $('panel-login').classList.toggle('hidden', !isLogin);
  $('panel-signup').classList.toggle('hidden', isLogin);

  $('tab-login').classList.toggle('active', isLogin);
  $('tab-login').setAttribute('aria-selected', String(isLogin));

  $('tab-signup').classList.toggle('active', !isLogin);
  $('tab-signup').setAttribute('aria-selected', String(!isLogin));
}

$('tab-login').addEventListener('click',  () => showPanel('login'));
$('tab-signup').addEventListener('click', () => showPanel('signup'));
$('go-signup').addEventListener('click',  () => showPanel('signup'));
$('go-login').addEventListener('click',   () => showPanel('login'));

// ── login ──────────────────────────────────────────────────────────────────
$('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();
  const fd = new FormData(e.currentTarget);
  setLoading('login-submit', true);

  try {
    const data = await apiPost('/login', {
      username_or_email: fd.get('username_or_email'),
      password: fd.get('password'),
    });
    localStorage.setItem('zylo_token', data.access_token);
    localStorage.setItem('zylo_username', data.user.username);
    window.location.replace('/chat');
  } catch (err) {
    showAlert(err.message);
  } finally {
    setLoading('login-submit', false);
  }
});

// ── signup ─────────────────────────────────────────────────────────────────
$('signup-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();
  const fd = new FormData(e.currentTarget);
  setLoading('signup-submit', true);

  try {
    const data = await apiPost('/signup', {
      username: fd.get('username'),
      email: fd.get('email'),
      password: fd.get('password'),
    });
    showPanel('login');
    showAlert(`✓ Account "${data.username}" created — sign in now.`, 'success');
    e.currentTarget.reset();
  } catch (err) {
    showAlert(err.message);
  } finally {
    setLoading('signup-submit', false);
  }
});