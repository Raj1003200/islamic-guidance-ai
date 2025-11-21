const API_URL = 'http://localhost:3000/api/guidance';

const form = document.getElementById('guidanceForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const loader = submitBtn.querySelector('.loader');
const errorDiv = document.getElementById('error');
const resultsDiv = document.getElementById('results');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Reset UI
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'none';
    
    // Get form data
    const problem = document.getElementById('problem').value.trim();
    const hadithBook = document.getElementById('hadithBook').value;
    
    if (!problem) {
        showError('Please enter your problem');
        return;
    }
    
    // Show loading state
    setLoading(true);
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ problem, hadithBook })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong');
        }
        
        displayResults(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    if (isLoading) {
        btnText.style.display = 'none';
        loader.style.display = 'inline-block';
    } else {
        btnText.style.display = 'inline';
        loader.style.display = 'none';
    }
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function displayResults(data) {
    // Display advice
    const adviceContent = document.getElementById('adviceContent');
    adviceContent.innerHTML = `<p>${formatText(data.advice)}</p>`;
    
    // Display Quran verses
    const quranContent = document.getElementById('quranContent');
    if (data.sources.quran && data.sources.quran.length > 0) {
        quranContent.innerHTML = data.sources.quran.map(verse => `
            <div class="verse-item">
                <p>${verse.text}</p>
                <span class="verse-reference">Surah ${verse.surah}, Verse ${verse.numberInSurah}</span>
            </div>
        `).join('');
    } else {
        quranContent.innerHTML = '<p>No Quran verses found for this topic.</p>';
    }
    
    // Display Hadith
    const hadithContent = document.getElementById('hadithContent');
    if (data.sources.hadith) {
        hadithContent.innerHTML = `
            <div class="verse-item">
                <p>${data.sources.hadith.text}</p>
            </div>
        `;
    } else {
        hadithContent.innerHTML = '<p>No Hadith found for this topic.</p>';
    }
    
    // Show results
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatText(text) {
    // Convert newlines to <br> and preserve formatting
    return text.replace(/\n/g, '<br>');
}
