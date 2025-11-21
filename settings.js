// settings.js – Handles API key storage, theme toggle, and logging

const apiKeyInput = document.getElementById('apiKey');
const saveBtn = document.getElementById('saveKeyBtn');
const themeSwitch = document.getElementById('themeSwitch');
const logDiv = document.getElementById('logOutput');

function log(message) {
  console.log(message);
  const p = document.createElement('p');
  p.textContent = message;
  logDiv.appendChild(p);
  logDiv.classList.remove('hidden');
}

// Load stored API key (masked) and theme on page load
window.addEventListener('DOMContentLoaded', () => {
  const storedKey = localStorage.getItem('geminiApiKey');
  if (storedKey) {
    apiKeyInput.value = storedKey;
    log('Loaded saved API key.');
  }
  const storedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', storedTheme);
  themeSwitch.checked = storedTheme === 'dark';
  log(`Applied stored theme: ${storedTheme}`);
});

saveBtn.addEventListener('click', () => {
  const key = apiKeyInput.value.trim();
  if (key.length === 0) {
    log('Attempted to save empty API key – ignored.');
    return;
  }
  localStorage.setItem('geminiApiKey', key);
  log('API key saved to localStorage.');
});

themeSwitch.addEventListener('change', () => {
  const newTheme = themeSwitch.checked ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  log(`Theme switched to ${newTheme}.`);
});
