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

function updateToggleIcons(theme) {
  if (!darkModeToggle) return;
  const moonIcon = darkModeToggle.querySelector('.moon-icon');
  const sunIcon = darkModeToggle.querySelector('.sun-icon');
  
  if (theme === 'dark' || theme === 'traditional') {
    moonIcon.classList.add('hidden');
    sunIcon.classList.remove('hidden');
  } else {
    moonIcon.classList.remove('hidden');
    sunIcon.classList.add('hidden');
  }
}

// Initial icon state
updateToggleIcons(document.documentElement.getAttribute('data-theme'));

// Listen for theme changes from other tabs/pages
window.addEventListener('storage', (e) => {
    if (e.key === 'theme') {
        const newTheme = e.newValue;
        document.documentElement.setAttribute('data-theme', newTheme);
        if (themeSelect) themeSelect.value = newTheme;
        updateToggleIcons(newTheme);
    }
});

if (darkModeToggle) {
  darkModeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    let newTheme;
    
    if (currentTheme === 'dark') {
      // Revert to previous theme or default
      newTheme = localStorage.getItem('previousTheme') || 'traditional';
    } else {
      // Save current theme as previous before switching to dark
      localStorage.setItem('previousTheme', currentTheme);
      newTheme = 'dark';
    }
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    if (themeSelect) {
      themeSelect.value = newTheme;
    }
    
    updateToggleIcons(newTheme);
  });
}

// Load stored API key (masked) on page load
window.addEventListener('DOMContentLoaded', async () => {
  // First try to load from backend .env
  try {
    const response = await fetch('/api/get-settings');
    if (response.ok) {
      const data = await response.json();
      if (data.apiKey) {
        apiKeyInput.value = data.apiKey;
      }
    }
  } catch (err) {
    console.error('Could not load settings from server.');
  }

  // Fallback to localStorage
  if (!apiKeyInput.value) {
    const storedKey = localStorage.getItem('geminiApiKey');
    if (storedKey) {
      apiKeyInput.value = storedKey;
    }
  }
  
  // Load available Gemini models
  await loadModels();
});

// =============================================================================
// GEMINI MODEL SELECTION
// =============================================================================

const modelSelect = document.getElementById('modelSelect');
const modelInfo = document.getElementById('modelInfo');

async function loadModels() {
  try {
    const response = await fetch('/api/models');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.success && data.models) {
      // Clear loading option
      modelSelect.innerHTML = '';
      
      // Populate dropdown with models
      data.models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        
        // Mark current model as selected
        if (model.id === data.current_model) {
          option.selected = true;
        }
        
        modelSelect.appendChild(option);
      });
      
      // Update model info for current selection
      updateModelInfo(data.current_model, data.models);
      
      console.log(`Loaded ${data.models.length} Gemini models`);
    }
  } catch (err) {
    console.error('Failed to load models:', err);
    modelSelect.innerHTML = '<option value="">Failed to load models</option>';
    modelInfo.textContent = 'Error loading models. Please refresh the page.';
    modelInfo.style.color = '#e74c3c';
  }
}

function updateModelInfo(modelId, models) {
  const model = models.find(m => m.id === modelId);
  if (model) {
    const inputTokens = (model.input_tokens / 1000).toFixed(0) + 'K';
    const outputTokens = (model.output_tokens / 1000).toFixed(0) + 'K';
    modelInfo.textContent = `Input: ${inputTokens} tokens | Output: ${outputTokens} tokens`;
    modelInfo.style.color = 'var(--text-secondary)';
  }
}

// Handle model selection change
if (modelSelect) {
  modelSelect.addEventListener('change', async (e) => {
    const selectedModelId = e.target.value;
    
    if (!selectedModelId) return;
    
    try {
      // Show loading state
      const originalText = e.target.selectedOptions[0].text;
      e.target.selectedOptions[0].text = originalText + ' (Switching...)';
      
      const response = await fetch('/api/models/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelId: selectedModelId })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Update info display
        const models = Array.from(modelSelect.options).map(opt => ({
          id: opt.value,
          name: opt.text,
          input_tokens: 0,
          output_tokens: 0
        }));
        
        // Fetch full model data
        const modelsResponse = await fetch('/api/models');
        if (modelsResponse.ok) {
          const modelsData = await modelsResponse.json();
          updateModelInfo(selectedModelId, modelsData.models);
        }
        
        showStatus(`Model changed to ${data.model.name}! Takes effect immediately.`);
        
        // Restore original text
        e.target.selectedOptions[0].text = originalText;
      } else {
        const error = await response.json();
        showStatus(`Failed to change model: ${error.detail}`, true);
        
        // Revert selection
        await loadModels();
      }
    } catch (err) {
      showStatus(`Error changing model: ${err.message}`, true);
      console.error('Model change error:', err);
      
      // Reload models to reset selection
      await loadModels();
    }
  });
}

// =============================================================================
// API KEY MANAGEMENT
// =============================================================================


saveBtn.addEventListener('click', async () => {
  const key = apiKeyInput.value.trim();
  if (key.length === 0) {
    showStatus('Please enter a valid API key.', true);
    return;
  }
  
  // Save to backend .env file
  try {
    const theme = document.documentElement.getAttribute('data-theme') || 'traditional';
    const model = document.getElementById('modelSelect').value;

    const response = await fetch('/api/save-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        apiKey: key,
        theme: theme,
        geminiModel: model
      })
    });
    
    if (response.ok) {
      showStatus('Settings saved successfully!');
    } else {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        const error = await response.json();
        showStatus(`Failed to save settings: ${error.detail || error.message}`, true);
      } else {
        showStatus(`Failed to save settings: Server returned ${response.status}`, true);
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

// =============================================================================
// CACHE MANAGEMENT
// =============================================================================

const clearCacheBtn = document.getElementById('clearCacheBtn');

if (clearCacheBtn) {
  clearCacheBtn.addEventListener('click', async () => {
    // Show confirmation dialog
    const confirmed = confirm(
      'Clear Cache\n\n' +
      'This will clear all cached data including:\n' +
      'Quran search results\n' +
      'Hadith collections\n' +
      'Guidance responses\n' +
      'Keywords\n' +
      'Rate limits\n\n' +
      'Are you sure you want to proceed?'
    );
    
    if (!confirmed) {
      return;
    }
    
    // Disable button and show loading state
    clearCacheBtn.disabled = true;
    const originalText = clearCacheBtn.textContent;
    clearCacheBtn.textContent = 'Clearing...';
    
    try {
      const response = await fetch('/api/admin/clear-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Clear local storage as well
        localStorage.clear();
        sessionStorage.clear();
        
        showStatus(`Cache cleared successfully!\n`);
        console.log('[CACHE] Cleared patterns:', data.patterns);
      } else {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        showStatus(`Failed to clear cache: ${error.detail}`, true);
      }
    } catch (err) {
      showStatus(`Error clearing cache: ${err.message}`, true);
      console.error('[CACHE] Clear error:', err);
    } finally {
      // Re-enable button
      clearCacheBtn.disabled = false;
      clearCacheBtn.textContent = originalText;
    }
  });
}

// =============================================================================
// NEW BUTTONS LOGIC
// =============================================================================

const loadSettingsBtn = document.getElementById('loadSettingsBtn');
const helpBtn = document.getElementById('helpBtn');
const creditsBtn = document.getElementById('creditsBtn');
const creditsModal = document.getElementById('creditsModal');
const closeModal = document.querySelector('.close-modal');

if (loadSettingsBtn) {
  loadSettingsBtn.addEventListener('click', async () => {
    try {
      const response = await fetch('/api/get-settings');
      if (response.ok) {
        const data = await response.json();
        
        // 1. Load API Key
        if (data.apiKey) {
          apiKeyInput.value = data.apiKey;
          localStorage.setItem('geminiApiKey', data.apiKey);
        }
        
        // 2. Load Theme
        if (data.theme) {
          document.documentElement.setAttribute('data-theme', data.theme);
          localStorage.setItem('theme', data.theme);
          if (themeSelect) {
            themeSelect.value = data.theme;
          }
        }
        
        // 3. Load Model
        if (data.geminiModel) {
           if (modelSelect) {
             modelSelect.value = data.geminiModel;
           }
        }

        showStatus('Settings loaded successfully!');
      } else {
        showStatus('Failed to load settings from server.', true);
      }
    } catch (err) {
      console.error('Could not load settings:', err);
      showStatus('Error loading settings.', true);
    }
  });
}

if (helpBtn) {
  helpBtn.addEventListener('click', () => {
    window.open('https://github.com/haseeb-heaven/islamic-guidance-ai/blob/develop/README.md', '_blank');
  });
}

if (creditsBtn && creditsModal) {
  creditsBtn.addEventListener('click', () => {
    creditsModal.classList.remove('hidden');
  });
}

if (closeModal && creditsModal) {
  closeModal.addEventListener('click', () => {
    creditsModal.classList.add('hidden');
  });
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
  if (e.target === creditsModal) {
    creditsModal.classList.add('hidden');
  }
});
