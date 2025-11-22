// settings.js – Handles API key storage, theme toggle, and logging

const apiKeyInput = document.getElementById('apiKey');
const saveBtn = document.getElementById('saveKeyBtn');
const statusDiv = document.getElementById('statusMessage');
const toggleVisibilityBtn = document.getElementById('toggleApiKeyVisibility');

function showStatus(message, isError = false) {
  statusDiv.textContent = message;
  statusDiv.classList.remove('hidden');
  statusDiv.style.color = isError ? '#e74c3c' : '#27ae60';
  setTimeout(() => {
    statusDiv.classList.add('hidden');
  }, 5000);
}

// Load stored API key (masked) on page load
window.addEventListener('DOMContentLoaded', async () => {
  // First try to load from backend .env
  try {
    const response = await fetch('/api/get-api-key');
    if (response.ok) {
      const data = await response.json();
      if (data.apiKey) {
        apiKeyInput.value = data.apiKey;
      }
    }
  } catch (err) {
    console.error('Could not load API key from server.');
  }

  // Fallback to localStorage
  if (!apiKeyInput.value) {
    const storedKey = localStorage.getItem('geminiApiKey');
    if (storedKey) {
      apiKeyInput.value = storedKey;
    }
  }
});

saveBtn.addEventListener('click', async () => {
  const key = apiKeyInput.value.trim();
  if (key.length === 0) {
    showStatus('Please enter a valid API key.', true);
    return;
  }
  
  // Save to backend .env file
  try {
    const response = await fetch('/api/save-api-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiKey: key })
    });
    
    if (response.ok) {
      showStatus('API key saved successfully! Please restart the server.');
    } else {
      const error = await response.json();
      showStatus(`Failed to save API key: ${error.detail}`, true);
    }
  } catch (err) {
    showStatus(`Network error: ${err.message}`, true);
  }
  
  // Also save to localStorage as backup
  localStorage.setItem('geminiApiKey', key);
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

