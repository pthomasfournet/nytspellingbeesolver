// ===========================
// State Management
// ===========================

const STORAGE_KEY = 'spelling-bee-solver-state';
const PROGRESS_KEY = 'spelling-bee-progress';

const state = {
    results: [],
    showConfidence: true,
    currentPuzzle: null,
    foundWords: new Set(),      // Words user has found in NYT
    invalidWords: new Set(),    // Words user flagged as invalid
    missedWords: new Set(),     // Words user found but solver missed
    totalPoints: 0,             // Points for found words
    maxPoints: 0                // Maximum possible points
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
// Progress Tracking (Per Puzzle)
// ===========================

function getPuzzleKey() {
    if (!state.currentPuzzle) return null;
    return state.currentPuzzle.letters.toLowerCase();
}

function saveProgress() {
    const puzzleKey = getPuzzleKey();
    if (!puzzleKey) return;

    try {
        const allProgress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}');
        allProgress[puzzleKey] = {
            foundWords: Array.from(state.foundWords),
            invalidWords: Array.from(state.invalidWords),
            missedWords: Array.from(state.missedWords),
            totalPoints: state.totalPoints,
            timestamp: Date.now()
        };
        localStorage.setItem(PROGRESS_KEY, JSON.stringify(allProgress));
    } catch (err) {
        console.warn('Failed to save progress:', err);
    }
}

function loadProgress() {
    const puzzleKey = getPuzzleKey();
    if (!puzzleKey) return;

    try {
        const allProgress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}');
        const puzzleProgress = allProgress[puzzleKey];

        if (puzzleProgress) {
            state.foundWords = new Set(puzzleProgress.foundWords || []);
            state.invalidWords = new Set(puzzleProgress.invalidWords || []);
            state.missedWords = new Set(puzzleProgress.missedWords || []);
            state.totalPoints = puzzleProgress.totalPoints || 0;
            console.log(`📦 Loaded progress: ${state.foundWords.size} found, ${state.invalidWords.size} invalid, ${state.missedWords.size} missed`);
        }
    } catch (err) {
        console.warn('Failed to load progress:', err);
    }
}

function clearProgress() {
    const puzzleKey = getPuzzleKey();
    if (!puzzleKey) return;

    try {
        const allProgress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}');
        delete allProgress[puzzleKey];
        localStorage.setItem(PROGRESS_KEY, JSON.stringify(allProgress));

        state.foundWords.clear();
        state.invalidWords.clear();
        state.missedWords.clear();
        state.totalPoints = 0;
    } catch (err) {
        console.warn('Failed to clear progress:', err);
    }
}

// ===========================
// NYT-Style Scoring
// ===========================

function calculateWordPoints(word, isPangram) {
    if (word.length === 4) return 1;
    if (isPangram) return word.length + 7;
    return word.length;
}

function calculateTotalScore() {
    let total = 0;
    state.foundWords.forEach(word => {
        const wordData = state.results.find(r => r.word === word);
        if (wordData) {
            total += calculateWordPoints(word, wordData.is_pangram);
        }
    });
    state.totalPoints = total;
    return total;
}

function calculateMaxScore() {
    let max = 0;
    state.results.forEach(wordData => {
        max += calculateWordPoints(wordData.word, wordData.is_pangram);
    });
    state.maxPoints = max;
    return max;
}

// ===========================
// Word Interaction
// ===========================

function toggleWordFound(word) {
    if (state.foundWords.has(word)) {
        state.foundWords.delete(word);
    } else {
        state.foundWords.add(word);
        // Can't be both found and invalid
        state.invalidWords.delete(word);
    }
    calculateTotalScore();
    saveProgress();
    renderResults();
    updateStats();
}

function toggleWordInvalid(word) {
    if (state.invalidWords.has(word)) {
        state.invalidWords.delete(word);
    } else {
        state.invalidWords.add(word);
        // Can't be both found and invalid
        state.foundWords.delete(word);
    }
    calculateTotalScore();
    saveProgress();
    renderResults();
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
    missedGroup: document.getElementById('missedGroup'),
    missedList: document.getElementById('missedList'),
    pangramsGroup: document.getElementById('pangramsGroup'),
    pangramsList: document.getElementById('pangramsList'),
    wordsContainer: document.getElementById('wordsContainer'),

    // Stats
    totalFoundStat: document.getElementById('totalFound'),
    remainingStat: document.getElementById('remaining'),
    progressStat: document.getElementById('progress'),
    pangramsStat: document.getElementById('pangrams'),
    progressBarFill: document.getElementById('progressBarFill'),
    progressPercent: document.getElementById('progressPercent'),

    // Controls
    toggleConfidenceBtn: document.getElementById('toggleConfidence'),
    copyAllBtn: document.getElementById('copyAll'),
    copyListBtn: document.getElementById('copyList'),
    exportInvalidBtn: document.getElementById('exportInvalid'),

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

// Export invalid words
elements.exportInvalidBtn.addEventListener('click', exportInvalidWords);

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

        // Identify missed words (words user found but solver didn't)
        // Combine results + excluded to get ALL words solver found
        const allSolverWords = new Set([
            ...data.results.map(r => r.word),
            ...(data.excluded_words || [])
        ]);

        state.missedWords.clear();
        excludeWords.forEach(word => {
            if (!allSolverWords.has(word)) {
                state.missedWords.add(word);
            }
        });

        if (state.missedWords.size > 0) {
            console.log(`⚠️  Solver missed ${state.missedWords.size} words that NYT accepted:`, Array.from(state.missedWords));
        }

        // Load progress for this puzzle and calculate scores
        loadProgress();
        calculateMaxScore();
        calculateTotalScore();

        // Render results
        renderStats(data.stats);
        renderResults();
        updateStats();

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
    elements.missedList.innerHTML = '';
    elements.pangramsList.innerHTML = '';
    elements.wordsContainer.innerHTML = '';

    // Render missed words (if any)
    if (state.missedWords.size > 0) {
        elements.missedGroup.classList.remove('hidden');
        const missedWordsArray = Array.from(state.missedWords).sort();

        elements.missedList.innerHTML = missedWordsArray.map(word => {
            return `
                <div class="word-item missed-word" data-word="${word}">
                    <span class="word-text">${word}</span>
                    <span class="word-status">⚠️</span>
                </div>
            `;
        }).join('');
    } else {
        elements.missedGroup.classList.add('hidden');
    }

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
        const word = item.dataset.word;

        // Left click: Toggle found status
        item.addEventListener('click', (e) => {
            e.preventDefault();
            toggleWordFound(word);
        });

        // Right click: Show context menu
        item.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            showContextMenu(word, e.clientX, e.clientY);
        });

        // Long press for mobile (500ms)
        let longPressTimer;
        item.addEventListener('touchstart', (e) => {
            longPressTimer = setTimeout(() => {
                e.preventDefault();
                const touch = e.touches[0];
                showContextMenu(word, touch.clientX, touch.clientY);
            }, 500);
        });

        item.addEventListener('touchend', () => {
            clearTimeout(longPressTimer);
        });

        item.addEventListener('touchmove', () => {
            clearTimeout(longPressTimer);
        });
    });
}

function createWordItem(wordData, isPangram) {
    const word = wordData.word;
    const isFound = state.foundWords.has(word);
    const isInvalid = state.invalidWords.has(word);

    const confidenceHtml = state.showConfidence
        ? `<span class="word-confidence">${wordData.confidence}%</span>`
        : '';

    const statusIcon = isFound ? '✓' : (isInvalid ? '🚩' : '');
    const stateClasses = isFound ? 'found' : (isInvalid ? 'invalid' : '');

    return `
        <div class="word-item ${isPangram ? 'pangram' : ''} ${stateClasses}"
             data-word="${word}"
             data-is-pangram="${isPangram}">
            <span class="word-text">${word}</span>
            ${confidenceHtml}
            ${statusIcon ? `<span class="word-status">${statusIcon}</span>` : ''}
        </div>
    `;
}

// ===========================
// Context Menu
// ===========================

function showContextMenu(word, x, y) {
    // Remove any existing context menu
    const existing = document.querySelector('.context-menu');
    if (existing) existing.remove();

    // Create context menu
    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;

    menu.innerHTML = `
        <button class="context-menu-item" data-action="copy">
            📋 Copy Word
        </button>
        <button class="context-menu-item" data-action="invalid">
            🚩 Report Invalid
        </button>
        <button class="context-menu-item" data-action="cancel">
            ✖ Cancel
        </button>
    `;

    document.body.appendChild(menu);

    // Handle menu actions
    menu.querySelectorAll('.context-menu-item').forEach(item => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;

            if (action === 'copy') {
                copyToClipboard(word);
                showToast(`Copied: ${word}`, 'success');
            } else if (action === 'invalid') {
                toggleWordInvalid(word);
                showToast(`Flagged as invalid: ${word}`, 'success');
            }

            menu.remove();
        });
    });

    // Close menu on outside click
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 100);
}

// ===========================
// Stats Update
// ===========================

function updateStats() {
    if (!state.currentPuzzle) return;

    const totalWords = state.results.length;
    const foundCount = state.foundWords.size;
    const remainingCount = totalWords - foundCount;

    // Calculate progress by points (NYT-style)
    const pointsProgressPercent = state.maxPoints > 0
        ? Math.round((state.totalPoints / state.maxPoints) * 100)
        : 0;

    // Count found pangrams
    const foundPangrams = Array.from(state.foundWords).filter(word => {
        const wordData = state.results.find(r => r.word === word);
        return wordData && wordData.is_pangram;
    }).length;

    const totalPangrams = state.results.filter(r => r.is_pangram).length;

    // Update stats cards
    elements.totalFoundStat.textContent = `${foundCount} / ${totalWords}`;
    elements.remainingStat.textContent = remainingCount;
    elements.progressStat.textContent = `${state.totalPoints} / ${state.maxPoints}`;
    elements.pangramsStat.textContent = `${foundPangrams} / ${totalPangrams}`;

    // Update progress bar
    if (elements.progressBarFill && elements.progressPercent) {
        elements.progressBarFill.style.width = `${pointsProgressPercent}%`;
        elements.progressPercent.textContent = `${pointsProgressPercent}%`;
    }

    console.log(`📊 Stats: ${foundCount}/${totalWords} words, ${state.totalPoints}/${state.maxPoints} points (${pointsProgressPercent}%)`);
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

function exportInvalidWords() {
    if (state.invalidWords.size === 0 && state.missedWords.size === 0) {
        showToast('No invalid or missed words to export', 'error');
        return;
    }

    // Create export data with puzzle context
    const exportData = {
        exported_at: new Date().toISOString(),
        puzzle: state.currentPuzzle,
        invalid_words: Array.from(state.invalidWords).map(word => {
            const wordData = state.results.find(r => r.word === word);
            return {
                word: word,
                type: 'false_positive',
                confidence: wordData ? wordData.confidence : null,
                is_pangram: wordData ? wordData.is_pangram : false,
                notes: 'Solver found this but user marked as invalid'
            };
        }),
        missed_words: Array.from(state.missedWords).map(word => {
            return {
                word: word,
                type: 'false_negative',
                confidence: null,
                is_pangram: false,
                notes: 'NYT accepted this but solver missed it'
            };
        })
    };

    // Create JSON blob and download
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `solver-feedback-${state.currentPuzzle.letters}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    const totalExported = state.invalidWords.size + state.missedWords.size;
    showToast(`Exported ${totalExported} words (${state.invalidWords.size} invalid, ${state.missedWords.size} missed)`, 'success');
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
