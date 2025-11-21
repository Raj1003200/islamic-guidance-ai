// script.js
// Handles validation, loading states, error handling, and result display for Islamic Guidance AI

const queryInput = document.getElementById('query');
const searchBtn = document.getElementById('searchBtn');
const statusDiv = document.getElementById('status');
const toastDiv = document.getElementById('toast');
const resultSection = document.getElementById('result');
const answerDiv = document.getElementById('answer');
const citationsDiv = document.getElementById('citations');

// Apply stored theme on load
const storedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', storedTheme);

// Utility to show toast messages
function showToast(message) {
  toastDiv.textContent = message;
  toastDiv.classList.remove('hidden');
  // Auto hide after animation (4s defined in CSS)
  setTimeout(() => {
    toastDiv.classList.add('hidden');
  }, 4000);
}

// Utility to update status text
function setStatus(text) {
  statusDiv.textContent = text;
  statusDiv.classList.remove('hidden');
}

function clearStatus() {
  statusDiv.textContent = '';
  statusDiv.classList.add('hidden');
}

// Validate input length
function isValidInput(text) {
  return text && text.trim().length >= 10;
}

// Simulate progressive status updates while awaiting backend response
function simulateLoadingStages(callback) {
  const stages = [
    'Understanding your problem...',
    'Searching Quran...',
    'Consulting Hadith...'
  ];
  let index = 0;
  const interval = setInterval(() => {
    setStatus(stages[index]);
    index++;
    if (index === stages.length) {
      clearInterval(interval);
      callback();
    }
  }, 1200); // change stage every 1.2s
}

async function fetchGuidance(query) {
  console.log('Fetching guidance for query:', query);
  try {
    // Placeholder endpoint – replace with real backend URL
    console.log('Sending POST request to /api/guidance');
    const response = await fetch('/api/guidance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    console.log('Response received. Status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Server error:', response.status, errorText);
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    console.log('Data parsed:', data);
    return data;
  } catch (err) {
    console.error('Network error:', err);
    return { error: 'Network error' };
  }
}

function displayResult(data) {
  // Hide status
  clearStatus();
  // Show result section
  resultSection.classList.remove('hidden');
  // Populate answer
  answerDiv.textContent = data.answer || '';
  // Populate citations if any
  citationsDiv.innerHTML = '';
  if (data.citations && data.citations.length) {
    const list = document.createElement('ul');
    data.citations.forEach((cite) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = cite.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = cite.title || cite.url;
      li.appendChild(a);
      list.appendChild(li);
    });
    citationsDiv.appendChild(list);
  }
}

searchBtn.addEventListener('click', async () => {
  const query = queryInput.value;
  if (!isValidInput(query)) {
    showToast('Please describe your situation in at least 10 characters.');
    return;
  }

  // Reset previous result
  resultSection.classList.add('hidden');
  answerDiv.textContent = '';
  citationsDiv.innerHTML = '';

  // Simulate loading stages then fetch
  simulateLoadingStages(async () => {
    const data = await fetchGuidance(query);
    if (data.error) {
      if (data.error === 'Irrelevant problem') {
        showToast("This doesn't seem to be a request for guidance. Please try describing a life situation.");
      } else {
        showToast('An error occurred. Please try again later.');
      }
      clearStatus();
      return;
    }
    displayResult(data);
  });
});

// Optional: allow Enter key to trigger search
queryInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    searchBtn.click();
  }
});
