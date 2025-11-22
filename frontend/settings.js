// settings.js – Handles API key storage, theme selection, and logging

const apiKeyInput = document.getElementById('apiKey');
const saveBtn = document.getElementById('saveKeyBtn');
const statusDiv = document.getElementById('statusMessage');
const toggleVisibilityBtn = document.getElementById('toggleApiKeyVisibility');
const themeSelect = document.getElementById('themeSelect');

function showStatus(message, isError = false) {
  statusDiv.textContent = message;
  statusDiv.classList.remove('hidden');
  statusDiv.style.color = isError ? '#e74c3c' : '#27ae60';
  setTimeout(() => {
    statusDiv.classList.add('hidden');
  }, 5000);
}

// Apply stored theme on load - Default to Traditional Islamic
const storedTheme = localStorage.getItem('theme') || 'traditional';
document.documentElement.setAttribute('data-theme', storedTheme);

// Set theme selector value on page load
if (themeSelect) {
  // Make sure the dropdown reflects the current theme
  themeSelect.value = storedTheme;
  
  themeSelect.addEventListener('change', (e) => {
    const selectedTheme = e.target.value;
    
    // Apply theme immediately
    document.documentElement.setAttribute('data-theme', selectedTheme);
    
    // Save preference
    localStorage.setItem('theme', selectedTheme);
    
    showStatus(`Theme changed to ${e.target.selectedOptions[0].text}!`);
  });
}

// Dark Mode Toggle
const darkModeToggle = document.getElementById('darkModeToggle');
if (darkModeToggle) {
  const moonIcon = darkModeToggle.querySelector('.moon-icon');
  const sunIcon = darkModeToggle.querySelector('.sun-icon');
  
  // Update icon based on current theme
  const currentTheme = document.documentElement.getAttribute('data-theme');
  if (currentTheme === 'dark') {
    moonIcon.classList.add('hidden');
    sunIcon.classList.remove('hidden');
  }
  
  darkModeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? (localStorage.getItem('theme') || 'traditional') : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    
    if (newTheme === 'dark') {
      moonIcon.classList.add('hidden');
      sunIcon.classList.remove('hidden');
    } else {
      moonIcon.classList.remove('hidden');
      sunIcon.classList.add('hidden');
      // Update theme selector to match
      if (themeSelect) {
        themeSelect.value = newTheme;
      }
    }
  });
}

// Load stored API key (masked) on page load
window.addEventListener('DOMContentLoaded', async () => {
  // First try to load from backend .env
  try {
    const response = await fetch('/api/get-api-key');
    if (response.ok) {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        const data = await response.json();
        if (data.apiKey) {
          apiKeyInput.value = data.apiKey;
        }
      } else {
        console.error('Server returned non-JSON response for get-api-key');
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
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        const error = await response.json();
        showStatus(`Failed to save API key: ${error.detail}`, true);
      } else {
        const text = await response.text();
        showStatus(`Failed to save API key: Server returned ${response.status} ${response.statusText}`, true);
        console.error("Server error:", text);
      }
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
