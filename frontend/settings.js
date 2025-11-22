// settings.js – Handles API key storage, theme toggle, and logging

const apiKeyInput = document.getElementById('apiKey');
const saveBtn = document.getElementById('saveKeyBtn');
const themeSwitch = document.getElementById('themeSwitch');
const logDiv = document.getElementById('logOutput');
const toggleVisibilityBtn = document.getElementById('toggleApiKeyVisibility');

function log(message) {
  console.log(message);
  const p = document.createElement('p');
  p.textContent = message;
  logDiv.appendChild(p);
  logDiv.classList.remove('hidden');
}

// Load stored API key (masked) and theme on page load
window.addEventListener('DOMContentLoaded', async () => {
  // First try to load from backend .env
  try {
    const response = await fetch('/api/get-api-key');
    if (response.ok) {
      const data = await response.json();
      if (data.apiKey) {
        apiKeyInput.value = data.apiKey;
        log('Loaded API key from server .env file.');
      }
    }
  } catch (err) {
    log('Could not load API key from server.');
  }

  // Fallback to localStorage
  if (!apiKeyInput.value) {
    const storedKey = localStorage.getItem('geminiApiKey');
    if (storedKey) {
      apiKeyInput.value = storedKey;
      log('Loaded saved API key from localStorage.');
    }
  }

  const storedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', storedTheme);
  themeSwitch.checked = storedTheme === 'dark';
  log(`Applied stored theme: ${storedTheme}`);
});

saveBtn.addEventListener('click', async () => {
  const key = apiKeyInput.value.trim();
  if (key.length === 0) {
    log('Attempted to save empty API key – ignored.');
    return;
  }
  
  // Save to backend .env file
  try {
    log('Saving API key to server...');
    const response = await fetch('/api/save-api-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiKey: key })
    });
    
    if (response.ok) {
      const data = await response.json();
      log('✓ API key saved to .env file successfully!');
      log('⚠ Please restart the server for changes to take effect.');
    } else {
      const error = await response.json();
      log(`✗ Failed to save API key: ${error.detail}`);
    }
  } catch (err) {
    log(`✗ Network error: ${err.message}`);
  }
  
  // Also save to localStorage as backup
  localStorage.setItem('geminiApiKey', key);
  log('✓ API key also saved to localStorage.');
});

themeSwitch.addEventListener('change', () => {
  const newTheme = themeSwitch.checked ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  log(`Theme switched to ${newTheme}.`);
});

// Password visibility toggle
if (toggleVisibilityBtn) {
  toggleVisibilityBtn.addEventListener('click', () => {
    const type = apiKeyInput.type === 'password' ? 'text' : 'password';
    apiKeyInput.type = type;
    
    const eyeOpen = toggleVisibilityBtn.querySelector('.eye-open');
    const eyeClosed = toggleVisibilityBtn.querySelector('.eye-closed');
    
    if (type === 'text') {
      eyeOpen.classList.add('hidden');
      eyeClosed.classList.remove('hidden');
    } else {
      eyeOpen.classList.remove('hidden');
      eyeClosed.classList.add('hidden');
    }
  });
}

