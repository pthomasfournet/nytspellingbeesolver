// ===========================
// State Management
// ===========================

const STORAGE_KEY = 'spelling-bee-solver-state';

const state = {
    results: [],
    showConfidence: true,
    currentPuzzle: null
};

// ===========================
// LocalStorage Persistence
// ===========================

function saveState() {
    try {
        const stateToSave = {
            center: elements.centerInput.value,
            others: elements.othersInput.value,
            knownWords: elements.knownWordsInput.value,
            showConfidence: state.showConfidence,
            timestamp: Date.now()
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    } catch (err) {
        console.warn('Failed to save state:', err);
    }
}

function loadState() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (!saved) return false;

        const savedState = JSON.parse(saved);

        // Check if saved state is less than 7 days old
        const age = Date.now() - savedState.timestamp;
        if (age > 7 * 24 * 60 * 60 * 1000) {
            clearState();
            return false;
        }

        // Restore inputs
        if (savedState.center) elements.centerInput.value = savedState.center;
        if (savedState.others) elements.othersInput.value = savedState.others;
        if (savedState.knownWords) elements.knownWordsInput.value = savedState.knownWords;
        if (savedState.showConfidence !== undefined) {
            state.showConfidence = savedState.showConfidence;
            elements.toggleConfidenceBtn.textContent = state.showConfidence ? '📊 Confidence' : '📊 Simple';
        }

        return true;
    } catch (err) {
        console.warn('Failed to load state:', err);
        return false;
    }
}

function clearState() {
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (err) {
        console.warn('Failed to clear state:', err);
    }
}

// ===========================
// DOM Elements
// ===========================

const elements = {
    // Inputs
    centerInput: document.getElementById('center'),
    othersInput: document.getElementById('others'),
    knownWordsInput: document.getElementById('knownWords'),
    solveBtn: document.getElementById('solveBtn'),
    toggleKnownBtn: document.getElementById('toggleKnown'),
    newPuzzleBtn: document.getElementById('newPuzzleBtn'),

    // Sections
    statsSection: document.getElementById('statsSection'),
    resultsSection: document.getElementById('resultsSection'),
    errorSection: document.getElementById('errorSection'),
    knownWordsSection: document.getElementById('knownWordsInput'),

    // Results
    pangramsGroup: document.getElementById('pangramsGroup'),
    pangramsList: document.getElementById('pangramsList'),
    wordsContainer: document.getElementById('wordsContainer'),

    // Stats
    totalFoundStat: document.getElementById('totalFound'),
    remainingStat: document.getElementById('remaining'),
    progressStat: document.getElementById('progress'),
    pangramsStat: document.getElementById('pangrams'),

    // Controls
    toggleConfidenceBtn: document.getElementById('toggleConfidence'),
    copyAllBtn: document.getElementById('copyAll'),
    copyListBtn: document.getElementById('copyList'),

    // Empty state
    emptyState: document.getElementById('emptyState'),

    // Toast
    toast: document.getElementById('toast'),
    errorMessage: document.getElementById('errorMessage')
};

// ===========================
// Event Listeners
// ===========================

// Toggle known words section
elements.toggleKnownBtn.addEventListener('click', () => {
    const isHidden = elements.knownWordsSection.classList.contains('hidden');
    elements.knownWordsSection.classList.toggle('hidden');

    const icon = elements.toggleKnownBtn.querySelector('span');
    icon.textContent = isHidden ? '➖' : '➕';
});

// New puzzle button
elements.newPuzzleBtn.addEventListener('click', () => {
    if (confirm('Start a new puzzle? This will clear all current data.')) {
        // Clear all inputs
        elements.centerInput.value = '';
        elements.othersInput.value = '';
        elements.knownWordsInput.value = '';

        // Hide results and stats
        elements.statsSection.classList.add('hidden');
        elements.resultsSection.classList.add('hidden');
        elements.errorSection.classList.add('hidden');

        // Hide known words section
        elements.knownWordsSection.classList.add('hidden');
        const icon = elements.toggleKnownBtn.querySelector('span');
        icon.textContent = '➕';

        // Clear state
        state.results = [];
        state.currentPuzzle = null;
        clearState();

        // Focus on center input
        elements.centerInput.focus();

        showToast('Ready for new puzzle!', 'success');
    }
});

// Solve button
elements.solveBtn.addEventListener('click', handleSolve);

// Toggle confidence display
elements.toggleConfidenceBtn.addEventListener('click', () => {
    state.showConfidence = !state.showConfidence;
    elements.toggleConfidenceBtn.textContent = state.showConfidence ? '📊 Confidence' : '📊 Simple';
    renderResults();
});

// Copy all words
elements.copyAllBtn.addEventListener('click', copyAllWords);

// Copy as list
elements.copyListBtn.addEventListener('click', copyWordsList);

// Auto-uppercase inputs and auto-save
elements.centerInput.addEventListener('input', (e) => {
    e.target.value = e.target.value.toUpperCase();
    saveState();

    // Auto-focus to other letters when center letter is filled
    if (e.target.value.length === 1) {
        elements.othersInput.focus();
    }
});

elements.othersInput.addEventListener('input', (e) => {
    e.target.value = e.target.value.toUpperCase();
    saveState();
});

elements.knownWordsInput.addEventListener('input', () => {
    saveState();
});

// Enter key to solve
elements.centerInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') elements.othersInput.focus();
});

elements.othersInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSolve();
});

// ===========================
// Main Functions
// ===========================

async function handleSolve() {
    // Validate inputs
    const center = elements.centerInput.value.trim().toLowerCase();
    const others = elements.othersInput.value.trim().toLowerCase();

    if (!center || center.length !== 1) {
        showError('Please enter a single center letter');
        return;
    }

    if (!others || others.length !== 6) {
        showError('Please enter exactly 6 other letters');
        return;
    }

    if (!/^[a-z]$/.test(center) || !/^[a-z]{6}$/.test(others)) {
        showError('Please use only letters (A-Z)');
        return;
    }

    // Parse known words
    const knownWordsText = elements.knownWordsInput.value.trim();
    const excludeWords = knownWordsText
        ? knownWordsText.split(/[,\s]+/).map(w => w.trim().toLowerCase()).filter(Boolean)
        : [];

    // Show loading state
    setLoading(true);
    hideError();

    try {
        // Call API
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                center_letter: center,
                other_letters: others,
                exclude_words: excludeWords.length > 0 ? excludeWords : null
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to solve puzzle');
        }

        const data = await response.json();

        // Update state
        state.results = data.results;
        state.currentPuzzle = data.puzzle;

        // Render results
        renderStats(data.stats);
        renderResults();

        // Show sections
        elements.statsSection.classList.remove('hidden');
        elements.resultsSection.classList.remove('hidden');

        // Show success toast
        showToast(`Found ${data.stats.remaining} words!`, 'success');

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

function renderStats(stats) {
    elements.totalFoundStat.textContent = stats.total_found;
    elements.remainingStat.textContent = stats.remaining;
    elements.progressStat.textContent = `${stats.progress_percent}%`;
    elements.pangramsStat.textContent = stats.pangram_count;
}

function renderResults() {
    // Clear existing results
    elements.pangramsList.innerHTML = '';
    elements.wordsContainer.innerHTML = '';

    // Check for empty results
    if (state.results.length === 0) {
        elements.emptyState.classList.remove('hidden');
        elements.pangramsGroup.classList.add('hidden');
        return;
    } else {
        elements.emptyState.classList.add('hidden');
    }

    // Separate pangrams and regular words
    const pangrams = state.results.filter(w => w.is_pangram);
    const regularWords = state.results.filter(w => !w.is_pangram);

    // Render pangrams
    if (pangrams.length > 0) {
        elements.pangramsGroup.classList.remove('hidden');
        elements.pangramsList.innerHTML = pangrams
            .map(word => createWordItem(word, true))
            .join('');
    } else {
        elements.pangramsGroup.classList.add('hidden');
    }

    // Group regular words by length
    const wordsByLength = {};
    regularWords.forEach(word => {
        if (!wordsByLength[word.length]) {
            wordsByLength[word.length] = [];
        }
        wordsByLength[word.length].push(word);
    });

    // Render word groups (sorted by length descending)
    const lengths = Object.keys(wordsByLength).map(Number).sort((a, b) => b - a);

    lengths.forEach(length => {
        const words = wordsByLength[length];
        const groupHtml = `
            <div class="word-group">
                <h3 class="group-title">${length}-letter words (${words.length})</h3>
                <div class="word-list">
                    ${words.map(w => createWordItem(w, false)).join('')}
                </div>
            </div>
        `;
        elements.wordsContainer.insertAdjacentHTML('beforeend', groupHtml);
    });

    // Add click handlers to word items
    document.querySelectorAll('.word-item').forEach(item => {
        item.addEventListener('click', () => {
            const word = item.dataset.word;
            copyToClipboard(word);
            showToast(`Copied: ${word}`, 'success');
        });
    });
}

function createWordItem(wordData, isPangram) {
    const confidenceHtml = state.showConfidence
        ? `<span class="word-confidence">${wordData.confidence}%</span>`
        : '';

    return `
        <div class="word-item ${isPangram ? 'pangram' : ''}" data-word="${wordData.word}">
            <span class="word-text">${wordData.word}</span>
            ${confidenceHtml}
        </div>
    `;
}

// ===========================
// Utility Functions
// ===========================

function setLoading(isLoading) {
    elements.solveBtn.disabled = isLoading;
    const btnText = elements.solveBtn.querySelector('.btn-text');
    const btnLoading = elements.solveBtn.querySelector('.btn-loading');

    if (isLoading) {
        btnText.classList.add('hidden');
        btnLoading.classList.remove('hidden');
    } else {
        btnText.classList.remove('hidden');
        btnLoading.classList.add('hidden');
    }
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorSection.classList.remove('hidden');
}

function hideError() {
    elements.errorSection.classList.add('hidden');
}

function showToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.classList.remove('hidden');

    setTimeout(() => {
        elements.toast.classList.add('hidden');
    }, 3000);
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        console.error('Failed to copy:', err);
    }
}

function copyAllWords() {
    const allWords = state.results.map(w => w.word).join(', ');
    copyToClipboard(allWords);
    showToast(`Copied ${state.results.length} words!`, 'success');
}

function copyWordsList() {
    const allWords = state.results.map(w => w.word).join('\n');
    copyToClipboard(allWords);
    showToast(`Copied ${state.results.length} words as list!`, 'success');
}

// ===========================
// Initialize
// ===========================

// Load saved state from LocalStorage
const stateLoaded = loadState();

if (stateLoaded) {
    console.log('📦 Restored previous puzzle state');
    // If known words section was filled, show it
    if (elements.knownWordsInput.value.trim()) {
        elements.knownWordsSection.classList.remove('hidden');
        const icon = elements.toggleKnownBtn.querySelector('span');
        icon.textContent = '➖';
    }
}

// Focus on center input on load
elements.centerInput.focus();

// Register service worker for PWA
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
        .then((registration) => {
            console.log('📱 PWA: Service Worker registered:', registration.scope);
        })
        .catch((error) => {
            console.log('❌ PWA: Service Worker registration failed:', error);
        });
}

// Log ready state
console.log('🐝 Spelling Bee Solver loaded and ready!');
