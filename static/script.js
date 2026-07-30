// Main application logic
document.addEventListener('DOMContentLoaded', function () {
    // Paperwhite Theme Switcher + lower-left ambient dock
    function ensureAmbientDock() {
        let dock = document.getElementById('uiAmbientDock');
        if (dock) return dock;

        dock = document.createElement('div');
        dock.id = 'uiAmbientDock';
        dock.className = 'ui-ambient-dock';
        dock.setAttribute('role', 'toolbar');
        dock.setAttribute('aria-label', 'Display and sound controls');
        dock.innerHTML = `
            <button type="button" id="ambientSoundBtn" class="ui-ambient-dock-btn ui-ambient-sound-btn" title="Mute ambient sound" aria-pressed="false" aria-label="Mute ambient sound">
                <svg class="sound-icon-on" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M11 5L6 9H3v6h3l5 4V5z"/>
                    <path d="M15.5 8.5a5 5 0 0 1 0 7"/>
                    <path d="M18 6a8 8 0 0 1 0 12"/>
                </svg>
                <svg class="sound-icon-off" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M11 5L6 9H3v6h3l5 4V5z"/>
                    <path d="M22 9l-6 6M16 9l6 6"/>
                </svg>
            </button>
            <button type="button" id="ambientBookBtn" class="ui-ambient-dock-btn ui-ambient-book-btn" title="Switch to Paperwhite reading mode" aria-pressed="false" aria-label="Switch to Paperwhite reading mode">
                <span class="book-3d" aria-hidden="true">
                    <span class="book-back"></span>
                    <span class="book-pages"></span>
                    <span class="book-front"></span>
                    <span class="book-spine"></span>
                </span>
            </button>
        `;
        document.body.appendChild(dock);

        const soundBtn = document.getElementById('ambientSoundBtn');
        const bookBtn = document.getElementById('ambientBookBtn');

        // Sound mute only matters when the dynamic hope experience is present
        if (!document.getElementById('hopeCanvas') && soundBtn) {
            soundBtn.hidden = true;
        }

        if (soundBtn) {
            soundBtn.addEventListener('click', () => {
                const muted = !window.isAmbientSoundMuted();
                localStorage.setItem('wwaijd_ambient_sound', muted ? 'muted' : 'on');
                updateAmbientSoundButton(muted);
            });
        }

        if (bookBtn) {
            bookBtn.addEventListener('click', () => window.toggleTheme());
        }

        return dock;
    }

    function updateAmbientSoundButton(muted) {
        const btn = document.getElementById('ambientSoundBtn');
        if (!btn) return;
        btn.classList.toggle('is-muted', muted);
        btn.setAttribute('aria-pressed', muted ? 'true' : 'false');
        btn.title = muted ? 'Unmute ambient sound' : 'Mute ambient sound';
        btn.setAttribute('aria-label', muted ? 'Unmute ambient sound' : 'Mute ambient sound');
    }

    window.isAmbientSoundMuted = function () {
        return localStorage.getItem('wwaijd_ambient_sound') === 'muted';
    };

    function updateThemeToggleButton(isPaperwhite, animate) {
        const bookBtn = document.getElementById('ambientBookBtn');
        if (!bookBtn) return;

        if (animate) {
            bookBtn.classList.add('is-animating');
            // Force reflow so opening/closing always plays
            void bookBtn.offsetWidth;
        }

        bookBtn.classList.toggle('is-open', isPaperwhite);
        bookBtn.setAttribute('aria-pressed', isPaperwhite ? 'true' : 'false');

        if (isPaperwhite) {
            bookBtn.title = 'Switch to Dynamic UI';
            bookBtn.setAttribute('aria-label', 'Switch to Dynamic UI (close book)');
        } else {
            bookBtn.title = 'Switch to Paperwhite reading mode';
            bookBtn.setAttribute('aria-label', 'Switch to Paperwhite reading mode (open book)');
        }

        if (animate) {
            window.setTimeout(() => bookBtn.classList.remove('is-animating'), 800);
        }

        // Keep legacy header buttons in sync if present (hidden via CSS)
        document.querySelectorAll('.theme-toggle-btn').forEach((btn) => {
            btn.innerHTML = isPaperwhite ? '✨ Dynamic UI' : '📖 Paperwhite';
            btn.setAttribute('aria-label', isPaperwhite
                ? 'Switch to Dynamic UI Mode'
                : 'Switch to Kindle Paperwhite Reader Mode');
        });
    }

    function initPaperwhiteTheme() {
        ensureAmbientDock();
        const savedTheme = localStorage.getItem('wwaijd_theme');
        const isPaperwhite = savedTheme === 'paperwhite';
        if (isPaperwhite) {
            document.body.classList.add('paperwhite-mode');
        }
        updateThemeToggleButton(isPaperwhite, false);
        updateAmbientSoundButton(window.isAmbientSoundMuted());
    }

    window.toggleTheme = function () {
        const bookBtn = document.getElementById('ambientBookBtn');
        const willBePaperwhite = !document.body.classList.contains('paperwhite-mode');

        // Play open/close first, then apply theme mid-animation
        if (bookBtn) {
            bookBtn.classList.add('is-animating');
            bookBtn.classList.toggle('is-open', willBePaperwhite);
        }

        window.setTimeout(() => {
            const isPaperwhite = document.body.classList.toggle('paperwhite-mode');
            localStorage.setItem('wwaijd_theme', isPaperwhite ? 'paperwhite' : 'ui');
            if (isPaperwhite && window.speechSynthesis && window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
            }
            updateThemeToggleButton(isPaperwhite, false);
        }, 280);
    };

    initPaperwhiteTheme();

    const form = document.getElementById('questionForm');
    const input = document.getElementById('questionInput');
    const askButton = document.getElementById('askButton');
    const buttonText = document.getElementById('buttonText');
    const btnIcon = document.getElementById('btnIcon');
    const btnLoader = document.getElementById('btnLoader');

    const responseSection = document.getElementById('responseSection');
    const answerText = document.getElementById('answerText');
    const passagesContainer = document.getElementById('passagesContainer');

    const errorSection = document.getElementById('errorSection');
    const errorText = document.getElementById('errorText');

    const loadingSection = document.getElementById('loadingSection');
    const questionPills = document.querySelectorAll('.question-pill');
    const modeButtons = document.querySelectorAll('.mode-button');
    const modeDescription = document.getElementById('modeDescription');
    const activeModePill = document.getElementById('activeModePill');
    const healthBadge = document.getElementById('healthBadge');
    const healthDetail = document.getElementById('healthDetail');
    const copyAnswerButton = document.getElementById('copyAnswerButton');
    const shareAnswerButton = document.getElementById('shareAnswerButton');
    const listenButton = document.getElementById('listenButton');
    const recentList = document.getElementById('recentQuestions');
    const clearRecentsButton = document.getElementById('clearRecentsButton');
    const sessionNotes = document.getElementById('sessionNotes');
    const saveNotesButton = document.getElementById('saveNotesButton');
    const notesStatus = document.getElementById('notesStatus');
    const searchCard = document.querySelector('.search-card');
    const streamStatusText = document.getElementById('streamStatusText');
    const streamMeter = document.getElementById('streamMeter');

    // Queue Elements
    const queueDisplay = document.getElementById('queueDisplay');
    const queuePeople = document.getElementById('queuePeople');
    const queuePosNum = document.getElementById('queuePosNum');

    // Quiz Elements
    const quizContainer = document.getElementById('quizContainer');
    const quizQuestionArea = document.getElementById('quizQuestionArea');
    const quizFeedback = document.getElementById('quizFeedback');
    const nextQuizBtn = document.getElementById('nextQuizBtn');
    let currentQuizData = null;

    // Tool Switcher Elements
    const toolButtons = document.querySelectorAll('.tool-button');
    const searchHeading = document.getElementById('searchHeading');
    let currentTool = 'ask';
    let currentMode = 'balanced';
    let lastResponseData = null;

    const RECENT_KEY = 'wwaijd:recent-questions';
    const NOTES_KEY = 'wwaijd:session-notes';

    const TOOL_CONFIG = {
        ask: {
            heading: 'Ask Athelstan your Bible question',
            placeholder: 'Ask Athelstan a question... (e.g., What does the Bible say about baptism?)',
            buttonText: 'Ask Athelstan',
            endpoint: '/api/ask-stream'
        },
        study: {
            heading: 'Generate a Bible Study',
            placeholder: 'Enter a topic... (e.g., Forgiveness, Patience, The Holy Spirit)',
            buttonText: 'Create Study',
            endpoint: '/api/study'
        },
        prayer: {
            heading: 'Generate a Prayer',
            placeholder: 'What do you need prayer for? (e.g., Strength for a job interview)',
            buttonText: 'Pray',
            endpoint: '/api/prayer'
        },
        parable: {
            heading: 'Generate a Modern Parable',
            placeholder: 'Enter a topic or situation... (e.g., Ambition, Family conflict, Wealth)',
            buttonText: 'Tell Story',
            endpoint: '/api/parable'
        },
        search: {
            heading: 'Search the Bible',
            placeholder: 'Search for passages... (e.g., love your neighbor)',
            buttonText: 'Search',
            endpoint: '/api/search'
        },
        quiz: {
            heading: 'Bible Quiz',
            placeholder: 'Enter a topic for the quiz... (e.g., David, Miracles, Faith) or leave blank for random',
            buttonText: 'Start Quiz',
            endpoint: '/api/quiz'
        }
    };

    const MODE_COPY = {
        balanced: 'A soft lean toward balanced, gentle guidance—Athelstan still chooses the form.',
        comfort: 'A soft lean toward encouragement and God\'s nearness.',
        clarity: 'A soft lean toward practical next steps when they help.',
        challenge: 'A soft lean toward loving conviction for growth.',
        blessing: 'A soft lean toward encouragement; a short blessing may close when it fits.'
    };

    // Chat Thread & Scroll Elements
    const chatMessages = document.getElementById('chatMessages');
    const chatWelcomeCard = document.getElementById('chatWelcomeCard');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const scrollToBottomBtn = document.getElementById('scrollToBottomBtn');
    const clearInputBtn = document.getElementById('clearInputBtn');
    let activeAiBubbleObj = null;
    let askAbortController = null;

    function startNewChat() {
        if (askAbortController) {
            askAbortController.abort();
            askAbortController = null;
        }
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        lastResponseData = null;
        activeAiBubbleObj = null;
        setStreamingState(false);
        hideError();
        hideQueue();
        hideLoading();
        if (chatMessages) {
            chatMessages.innerHTML = '';
            if (chatWelcomeCard) {
                chatWelcomeCard.style.display = 'flex';
                chatMessages.appendChild(chatWelcomeCard);
            }
        }
        if (scrollToBottomBtn) scrollToBottomBtn.style.display = 'none';
        if (input) {
            input.value = '';
            input.focus();
            if (typeof autoResizeInput === 'function') {
                autoResizeInput();
            } else {
                input.dispatchEvent(new Event('input'));
            }
        }
    }

    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', startNewChat);
    }

    if (chatMessages && scrollToBottomBtn) {
        chatMessages.addEventListener('scroll', () => {
            const isScrolledUp = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight > 120;
            scrollToBottomBtn.style.display = isScrolledUp ? 'inline-flex' : 'none';
        });

        scrollToBottomBtn.addEventListener('click', () => {
            chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
        });
    }

    function scrollToChatBottom() {
        if (!chatMessages) return;
        setTimeout(() => {
            chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
        }, 40);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function appendUserBubble(text) {
        if (!chatMessages) return;
        if (chatWelcomeCard) chatWelcomeCard.style.display = 'none';

        const userBubble = document.createElement('div');
        userBubble.className = 'chat-bubble user-bubble';
        userBubble.innerHTML = `
            <div class="user-bubble-content">${escapeHtml(text)}</div>
        `;
        chatMessages.appendChild(userBubble);
        scrollToChatBottom();
    }

    function createAiBubble(mode, questionText) {
        if (!chatMessages) return null;
        if (chatWelcomeCard) chatWelcomeCard.style.display = 'none';

        const bubbleId = 'ai-bubble-' + Date.now();
        const modeLabel = (mode || currentMode || 'balanced').charAt(0).toUpperCase() + (mode || currentMode || 'balanced').slice(1);

        const aiBubble = document.createElement('div');
        aiBubble.className = 'chat-bubble ai-bubble';
        aiBubble.id = bubbleId;
        aiBubble.innerHTML = `
            <div class="ai-bubble-header">
                <div class="ai-avatar-badge">
                    <span class="avatar-sparkle">✨</span>
                    <span class="avatar-title">Athelstan</span>
                </div>
                <span class="mode-pill">${modeLabel} focus</span>
            </div>
            <div class="ai-bubble-body answer-text">
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
            <div class="ai-passages-drawer" style="display: none;">
                <button type="button" class="passages-toggle-btn">
                    <span>📖 Scripture References (<span class="passages-count">0</span>)</span>
                    <span class="drawer-arrow">▼</span>
                </button>
                <div class="passages-drawer-content passages-container" style="display: none;"></div>
            </div>
            <div class="ai-bubble-actions" style="display: none;">
                <button type="button" class="ghost-button copy-msg-btn">📋 Copy</button>
                <button type="button" class="ghost-button share-msg-btn">🔗 Share</button>
                <button type="button" class="ghost-button listen-msg-btn">🔊 Listen</button>
            </div>
            <div class="ai-followups" style="display: none;"></div>
        `;

        chatMessages.appendChild(aiBubble);
        scrollToChatBottom();

        const toggleBtn = aiBubble.querySelector('.passages-toggle-btn');
        const drawerContent = aiBubble.querySelector('.passages-drawer-content');
        const arrow = aiBubble.querySelector('.drawer-arrow');

        if (toggleBtn && drawerContent) {
            toggleBtn.addEventListener('click', () => {
                const isHidden = drawerContent.style.display === 'none';
                drawerContent.style.display = isHidden ? 'grid' : 'none';
                if (arrow) arrow.textContent = isHidden ? '▲' : '▼';
            });
        }

        activeAiBubbleObj = {
            element: aiBubble,
            body: aiBubble.querySelector('.ai-bubble-body'),
            drawer: aiBubble.querySelector('.ai-passages-drawer'),
            drawerContent: drawerContent,
            countSpan: aiBubble.querySelector('.passages-count'),
            actions: aiBubble.querySelector('.ai-bubble-actions'),
            copyBtn: aiBubble.querySelector('.copy-msg-btn'),
            shareBtn: aiBubble.querySelector('.share-msg-btn'),
            listenBtn: aiBubble.querySelector('.listen-msg-btn'),
            followups: aiBubble.querySelector('.ai-followups')
        };

        return activeAiBubbleObj;
    }

    function renderBubblePassages(container, passages, version) {
        if (!container) return;
        container.innerHTML = '';

        passages.forEach(passage => {
            const item = document.createElement('div');
            item.className = 'passage-item bubble-passage-item';

            const ref = document.createElement('div');
            ref.className = 'passage-reference';
            ref.textContent = passage.reference || buildFallbackReference(passage);

            const text = document.createElement('div');
            text.className = 'passage-text';
            text.textContent = passage.text;

            const actions = document.createElement('div');
            actions.className = 'passage-actions';

            if (passage.source_path) {
                const link = document.createElement('a');
                link.href = buildPassageViewerUrl(passage);
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = 'View in Bible';
                actions.appendChild(link);
            }

            const copyBtn = document.createElement('button');
            copyBtn.type = 'button';
            copyBtn.textContent = 'Copy Reference';
            copyBtn.addEventListener('click', () => copyToClipboard(ref.textContent));
            actions.appendChild(copyBtn);

            item.appendChild(ref);
            item.appendChild(text);
            item.appendChild(actions);
            container.appendChild(item);
        });
    }

    function renderBubbleFollowups(container, promptText) {
        if (!container) return;
        container.innerHTML = '';
        container.style.display = 'flex';

        const followups = [
            { icon: '❤️', text: 'God\'s Love', query: `How does God's love apply to this situation?` },
            { icon: '🕊️', text: 'Pray for Love & Peace', query: `Please write a prayer filled with love & comfort for: ${promptText.slice(0, 60)}` },
            { icon: '🤝', text: 'How to Show Love', query: `How can I show Christ's love to others in this situation?` },
            { icon: '📖', text: 'Verses on Love', query: `What scriptures speak about God's love regarding this?` }
        ];

        followups.forEach(f => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'followup-chip-btn';
            btn.innerHTML = `<span>${f.icon}</span> ${f.text}`;
            btn.addEventListener('click', () => {
                input.value = f.query;
                autoResizeInput();
                form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            });
            container.appendChild(btn);
        });
    }

    function toggleSpeechSynthesis(text, btnElement) {
        if (!window.speechSynthesis) return;

        if (document.body.classList.contains('paperwhite-mode')) {
            if (window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
            }
            if (btnElement) btnElement.textContent = '🔊 Listen';
            return;
        }

        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            if (btnElement) btnElement.textContent = '🔊 Listen';
            return;
        }

        const cleanText = text.replace(/<[^>]*>?/gm, '').replace(/\*/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        utterance.onend = () => {
            if (btnElement) btnElement.textContent = '🔊 Listen';
        };

        if (btnElement) btnElement.textContent = '⏸️ Stop';
        window.speechSynthesis.speak(utterance);
    }

    document.querySelectorAll('.question-pill, .starter-pill').forEach((pill) => {
        pill.addEventListener('click', () => {
            if (currentTool !== 'ask') {
                switchTool('ask');
            }

            const preset = (pill.dataset.question || pill.textContent || '').trim();
            if (!preset) return;
            input.value = preset;
            autoResizeInput();
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
    });

    modeButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const mode = button.dataset.mode;
            if (mode) {
                setMode(mode);
            }
        });
    });

    input.addEventListener('focus', () => {
        if (searchCard) searchCard.classList.add('is-focused');
    });
    input.addEventListener('blur', () => {
        if (searchCard) searchCard.classList.remove('is-focused');
    });

    // Auto-resize textarea & Clear button handling
    function autoResizeInput() {
        input.style.height = 'auto';
        input.rows = 1;
        
        if (input.value) {
            input.style.height = input.scrollHeight + 'px';
        } else {
            const v = input.value;
            input.value = input.placeholder;
            const h = input.scrollHeight;
            input.value = v;
            input.style.height = h + 'px';
        }

        if (clearInputBtn) {
            clearInputBtn.style.display = input.value.trim() ? 'inline-flex' : 'none';
        }
    }

    input.addEventListener('input', autoResizeInput);

    if (clearInputBtn) {
        clearInputBtn.addEventListener('click', () => {
            input.value = '';
            clearInputBtn.style.display = 'none';
            autoResizeInput();
            input.focus();
        });
    }

    // Enter key sends message, Shift+Enter inserts newline
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (input.value.trim()) {
                form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        }
    });

    // Tool Switcher Logic
    toolButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tool = button.dataset.tool;
            if (tool && TOOL_CONFIG[tool]) {
                switchTool(tool);
            }
        });
    });

    function switchTool(tool) {
        currentTool = tool;
        const config = TOOL_CONFIG[tool];

        const prayerContainer = document.getElementById('prayerPublicContainer');
        const prayerCheck = document.getElementById('prayerPublicCheck');
        if (prayerContainer) {
            if (tool === 'prayer') {
                prayerContainer.style.display = 'flex';
            } else {
                prayerContainer.style.display = 'none';
                if (prayerCheck) prayerCheck.checked = false;
            }
        }

        toolButtons.forEach(btn => {
            const isActive = btn.dataset.tool === tool;
            btn.classList.toggle('is-active', isActive);
            btn.setAttribute('aria-selected', isActive);
        });

        if (searchHeading) searchHeading.textContent = config.heading;
        input.placeholder = config.placeholder;
        buttonText.textContent = config.buttonText;

        input.value = '';
        autoResizeInput();
        input.focus();

        hideResponse();
        hideError();

        if (quizContainer) quizContainer.style.display = 'none';
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const value = input.value.trim();
        if (!value) return;

        appendUserBubble(value);

        input.value = '';
        autoResizeInput();

        showLoading();
        hideResponse();
        hideError();

        try {
            if (currentTool === 'ask') {
                persistRecentQuestion(value);
                persistNotes();
                await askQuestionStream(value);
            } else if (currentTool === 'study') {
                await generateStudy(value);
            } else if (currentTool === 'prayer') {
                await generatePrayer(value);
            } else if (currentTool === 'parable') {
                await generateParable(value);
            } else if (currentTool === 'search') {
                await performSearch(value);
            } else if (currentTool === 'quiz') {
                await generateQuiz(value);
            }

        } catch (error) {
            console.error('Error:', error);
            displayError(error.message || 'An error occurred while processing your request. Please try again.');
            hideLoading();
        }
    });

    async function askQuestionStream(question) {
        const version = document.getElementById('versionSelector').value;
        if (askAbortController) {
            askAbortController.abort();
        }
        askAbortController = new AbortController();
        const signal = askAbortController.signal;
        setStreamingState(true);
        try {
            const response = await fetch('/api/ask-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question, mode: currentMode, version: version }),
                signal
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to get response');
            }

            await streamResponse(response, { mode: currentMode, question: question, version: version });
        } catch (err) {
            if (err && err.name === 'AbortError') {
                return;
            }
            throw err;
        } finally {
            if (askAbortController && askAbortController.signal === signal) {
                askAbortController = null;
            }
            setStreamingState(false);
        }
    }

    async function generateStudy(topic) {
        setStreamingState(true);
        try {
            const response = await fetch('/api/study-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to generate study');
            }

            await streamResponse(response, { mode: 'study', question: `Bible Study: ${topic}` });
        } finally {
            setStreamingState(false);
        }
    }

    async function generatePrayer(request) {
        setStreamingState(true);
        const isPublic = document.getElementById('prayerPublicCheck')?.checked || false;
        try {
            const response = await fetch('/api/prayer-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request: request, public: isPublic })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to generate prayer');
            }

            await streamResponse(response, { mode: 'prayer', question: `Prayer for: ${request}` });
        } finally {
            setStreamingState(false);
        }
    }

    async function generateParable(topic) {
        setStreamingState(true);
        try {
            const response = await fetch('/api/parable-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to generate parable');
            }

            await streamResponse(response, { mode: 'parable', question: `Parable about: ${topic}` });
        } finally {
            setStreamingState(false);
        }
    }

    async function performSearch(query) {
        setStreamingState(true);
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to search');
            }

            const data = await response.json();
            
            const currentBubble = createAiBubble('search', `Search: ${query}`);
            if (currentBubble) {
                currentBubble.body.innerHTML = `<p>Found <strong>${data.count}</strong> relevant passages for: <em>${query}</em></p>`;
                if (data.passages && data.passages.length > 0) {
                    currentBubble.countSpan.textContent = data.passages.length;
                    currentBubble.drawer.style.display = 'block';
                    currentBubble.drawerContent.style.display = 'grid';
                    renderBubblePassages(currentBubble.drawerContent, data.passages);
                }
            }

            displayPassages(data.passages);
            hideError();
            hideLoading();
            scrollToChatBottom();

        } finally {
            setStreamingState(false);
        }
    }

    async function generateQuiz(topic) {
        setStreamingState(true);
        try {
            const response = await fetch('/api/quiz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to generate quiz');
            }

            const data = await response.json();
            currentQuizData = data;

            renderQuiz(data);
            hideLoading();

        } finally {
            setStreamingState(false);
        }
    }

    async function streamResponse(response, context = {}) {
        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('Streaming is not supported in this browser.');
        }

        const decoder = new TextDecoder();
        let buffer = '';
        let accumulatedAnswer = '';
        let passages = [];
        let finished = false;

        const currentBubble = createAiBubble(context.mode || currentMode, context.question);

        if (answerText) answerText.innerHTML = '<span class="typing-cursor"></span>';
        hideError();
        hideLoading();
        setStreamingState(true);

        while (!finished) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const messages = buffer.split('\n\n');
            buffer = messages.pop();

            for (const message of messages) {
                if (!message.trim()) continue;
                const eventMatch = message.match(/event: ([\w-]+)\s+data: (.+)/s);
                if (!eventMatch) continue;

                const [, eventType, jsonData] = eventMatch;
                const data = JSON.parse(jsonData);

                if (data.mode) {
                    updateModeUI(data.mode);
                } else if (context.mode) {
                    updateModeUI(context.mode);
                }

                if (eventType === 'queue_update') {
                    handleQueueUpdate(data.position);
                } else if (eventType === 'passages') {
                    hideQueue();
                    passages = data.passages || [];
                    if (passages.length > 0 && currentBubble) {
                        currentBubble.countSpan.textContent = passages.length;
                        currentBubble.drawer.style.display = 'block';
                        renderBubblePassages(currentBubble.drawerContent, passages, data.version);
                    }
                    displayPassages(passages, data.version);
                } else if (eventType === 'chunk') {
                    hideQueue();
                    accumulatedAnswer += data.text || '';
                    const formattedHtml = renderMarkdown(accumulatedAnswer) + '<span class="typing-cursor"></span>';
                    
                    if (currentBubble) {
                        currentBubble.body.innerHTML = formattedHtml;
                    }
                    if (answerText) answerText.innerHTML = formattedHtml;
                    setupBibleRefHoverPreviews();
                    scrollToChatBottom();
                } else if (eventType === 'done') {
                    finished = true;
                    break;
                } else if (eventType === 'error') {
                    const errText = data.error || 'Streaming failed';
                    if (!accumulatedAnswer) {
                        accumulatedAnswer = `⚠️ *${errText}*`;
                    }
                    finished = true;
                    break;
                }
            }
        }

        hideQueue();
        const finalHtml = renderMarkdown(accumulatedAnswer);
        
        if (currentBubble) {
            currentBubble.body.innerHTML = finalHtml;
            currentBubble.actions.style.display = 'flex';
            
            currentBubble.copyBtn.addEventListener('click', () => copyToClipboard(accumulatedAnswer));
            currentBubble.shareBtn.addEventListener('click', () => shareConversation(context.question || '', accumulatedAnswer));
            currentBubble.listenBtn.addEventListener('click', () => toggleSpeechSynthesis(accumulatedAnswer, currentBubble.listenBtn));

            renderBubbleFollowups(currentBubble.followups, context.question || accumulatedAnswer);
        }

        if (answerText) answerText.innerHTML = finalHtml;
        setupBibleRefHoverPreviews();
        setStreamingState(false);
        scrollToChatBottom();

        lastResponseData = {
            question: context.question || input.value,
            answer: accumulatedAnswer,
            passages: passages,
            mode: currentMode
        };

        if (shareAnswerButton) {
            shareAnswerButton.textContent = 'Share';
            shareAnswerButton.disabled = false;
        }

        if (listenButton) {
            listenButton.textContent = 'Listen 🔊';
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
        }
    }

    function setStreamingState(isActive) {
        if (searchCard) {
            searchCard.classList.toggle('is-streaming', isActive);
        }
        if (streamMeter) {
            streamMeter.classList.toggle('is-live', isActive);
        }
        if (streamStatusText) {
            streamStatusText.textContent = isActive
                ? 'Responding live...'
                : 'Responses stream in real time.';
        }
    }

    function setMode(mode) {
        currentMode = MODE_COPY[mode] ? mode : 'balanced';
        updateModeUI(currentMode);
    }

    function updateModeUI(modeOverride) {
        const mode = modeOverride || currentMode;
        currentMode = mode;
        modeButtons.forEach((button) => {
            const isActive = button.dataset.mode === mode;
            button.classList.toggle('is-active', isActive);
        });
        if (modeDescription && MODE_COPY[mode]) {
            modeDescription.textContent = MODE_COPY[mode];
        }
        if (activeModePill) {
            const label = mode.charAt(0).toUpperCase() + mode.slice(1);
            activeModePill.textContent = `${label} focus`;
        }
    }

    function displayPassages(passages, version) {
        // Display Bible passages in the UI
        const heading = document.getElementById('passagesHeading');
        if (heading) {
            const ver = (version || 'KJV').toUpperCase();
            heading.textContent = `${ver} Biblical References`;
        }

        passagesContainer.innerHTML = '';

        // Reset animation by removing and re-adding the class
        passagesContainer.style.animation = 'none';
        setTimeout(() => {
            passagesContainer.style.animation = '';
        }, 10);

        if (passages && passages.length > 0) {
            passages.forEach(passage => {
                const passageDiv = document.createElement('div');
                passageDiv.className = 'passage-item';

                const reference = document.createElement('div');
                reference.className = 'passage-reference';
                reference.textContent = passage.reference || buildFallbackReference(passage);

                const meta = document.createElement('div');
                meta.className = 'passage-meta';
                const metaParts = [];
                if (passage.book) metaParts.push(passage.book);
                if (passage.chapter) metaParts.push(`Chapter ${passage.chapter}`);
                if (passage.testament) metaParts.push(passage.testament);
                if (metaParts.length) {
                    const metaText = document.createElement('span');
                    metaText.textContent = metaParts.join(' | ');
                    meta.appendChild(metaText);
                }
                if (typeof passage.relevance === 'number') {
                    const relevanceBadge = document.createElement('span');
                    relevanceBadge.className = 'relevance-badge';
                    relevanceBadge.textContent = `${Math.round(passage.relevance)}% match`;
                    meta.appendChild(relevanceBadge);
                }

                const text = document.createElement('div');
                text.className = 'passage-text';
                text.textContent = passage.text;

                const actions = document.createElement('div');
                actions.className = 'passage-actions';

                if (passage.source_path) {
                    const link = document.createElement('a');
                    link.href = buildPassageViewerUrl(passage);
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = 'View in Bible';
                    actions.appendChild(link);
                }

                const copyRefButton = document.createElement('button');
                copyRefButton.type = 'button';
                copyRefButton.textContent = 'Copy Reference';
                copyRefButton.addEventListener('click', () => copyToClipboard(reference.textContent));
                actions.appendChild(copyRefButton);

                passageDiv.appendChild(reference);
                if (metaParts.length || typeof passage.relevance === 'number') {
                    passageDiv.appendChild(meta);
                }
                passageDiv.appendChild(text);
                passageDiv.appendChild(actions);
                passagesContainer.appendChild(passageDiv);
            });
        }
    }

    function handleQueueUpdate(position) {
        if (!queueDisplay) return;

        queueDisplay.classList.remove('is-hidden');
        if (queuePosNum) queuePosNum.textContent = position;

        if (queuePeople) {
            // Update people icons based on position
            // e.g., if position is 3, show 2 people ahead
            let peopleHtml = '';
            // Show up to 5 people
            const peopleToShow = Math.min(position - 1, 5);
            for (let i = 0; i < peopleToShow; i++) {
                peopleHtml += '🧍';
            }
            if (position > 6) {
                peopleHtml += '...';
            }
            // Add "You" marker if desired, or just list people ahead
            queuePeople.innerHTML = peopleHtml;
        }
    }

    function hideQueue() {
        if (queueDisplay) {
            queueDisplay.classList.add('is-hidden');
        }
    }

    function showLoading() {
        loadingSection.style.display = 'block';
        askButton.disabled = true;
        if (btnIcon) btnIcon.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'flex';
    }

    function hideLoading() {
        loadingSection.style.display = 'none';
        askButton.disabled = false;
        if (btnIcon) btnIcon.style.display = 'flex';
        if (btnLoader) btnLoader.style.display = 'none';
    }

    function displayResponse(data) {
        // Display answer with Markdown formatting support
        answerText.innerHTML = renderMarkdown(data.answer);

        // Add hover preview listeners to Bible reference links
        setupBibleRefHoverPreviews();

        // Display passages
        passagesContainer.innerHTML = '';
        if (data.passages && data.passages.length > 0) {
            data.passages.forEach(passage => {
                const passageDiv = document.createElement('div');
                passageDiv.className = 'passage-item';

                const reference = document.createElement('div');
                reference.className = 'passage-reference';
                reference.textContent = passage.reference || buildFallbackReference(passage);

                const meta = document.createElement('div');
                meta.className = 'passage-meta';
                const metaParts = [];
                if (passage.book) metaParts.push(passage.book);
                if (passage.chapter) metaParts.push(`Chapter ${passage.chapter}`);
                if (passage.testament) metaParts.push(passage.testament);
                if (metaParts.length) {
                    const metaText = document.createElement('span');
                    metaText.textContent = metaParts.join(' | ');
                    meta.appendChild(metaText);
                }
                if (typeof passage.relevance === 'number') {
                    const relevanceBadge = document.createElement('span');
                    relevanceBadge.className = 'relevance-badge';
                    relevanceBadge.textContent = `${Math.round(passage.relevance)}% match`;
                    meta.appendChild(relevanceBadge);
                }

                const text = document.createElement('div');
                text.className = 'passage-text';
                text.textContent = passage.text;

                const actions = document.createElement('div');
                actions.className = 'passage-actions';

                if (passage.source_path) {
                    const link = document.createElement('a');
                    link.href = buildPassageViewerUrl(passage);
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = 'View in Bible';
                    actions.appendChild(link);
                }

                const copyRefButton = document.createElement('button');
                copyRefButton.type = 'button';
                copyRefButton.textContent = 'Copy Reference';
                copyRefButton.addEventListener('click', () => copyToClipboard(reference.textContent));
                actions.appendChild(copyRefButton);

                passageDiv.appendChild(reference);
                if (metaParts.length || typeof passage.relevance === 'number') {
                    passageDiv.appendChild(meta);
                }
                passageDiv.appendChild(text);
                passageDiv.appendChild(actions);
                passagesContainer.appendChild(passageDiv);
            });
        }

        responseSection.classList.remove('is-hidden');

        // Smooth scroll to response
        setTimeout(() => {
            responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    function hideResponse() {
        responseSection.classList.add('is-hidden');
    }

    function displayError(message) {
        errorText.textContent = message;
        errorSection.style.display = 'block';

        setTimeout(() => {
            errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    function hideError() {
        errorSection.style.display = 'none';
    }

    function renderMarkdown(markdownText) {
        if (!markdownText) {
            return '';
        }
        let html;
        if (window.marked) {
            const renderer = window.marked.use({ mangle: false, headerIds: false });
            html = renderer.parse(markdownText);
            html = window.DOMPurify ? DOMPurify.sanitize(html) : html;
        } else {
            html = markdownText
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n{2,}/g, '<br><br>');
        }

        // Add Bible reference links with hover preview
        html = linkifyBibleReferences(html);
        return html;
    }

    function linkifyBibleReferences(html) {
        // Pattern to match Bible references like "Proverbs 4:27" or "Matthew 5:3-10"
        // Matches: Book name (1-3 words) + Chapter:Verse or Chapter:Verse-Verse
        const bibleRefPattern = /\b((?:[1-3]\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(\d+):(\d+)(?:-(\d+))?/g;

        return html.replace(bibleRefPattern, (match, book, chapter, verseStart, verseEnd, offset, fullString) => {
            const reference = `${book.trim()} ${chapter}:${verseStart}${verseEnd ? '-' + verseEnd : ''}`;
            const dataAttrs = `data-book="${book.trim()}" data-chapter="${chapter}" data-verse-start="${verseStart}" data-verse-end="${verseEnd || verseStart}"`;
            const prevChar = offset > 0 ? fullString[offset - 1] : '';
            const priorSix = offset >= 6 ? fullString.slice(offset - 6, offset) : '';
            const hasNbspEntity = priorSix === '&nbsp;';
            const needsSpace = !hasNbspEntity && prevChar && !/\s|\(|>/.test(prevChar);
            const prefix = needsSpace ? ' ' : '';
            return `${prefix}<a href="#" class="bible-ref-link" ${dataAttrs} title="${reference}">${reference}</a>`;
        });
    }

    function buildPassageViewerUrl(passage) {
        if (passage.book && passage.chapter) {
            // Use version-aware URL if version is present, otherwise default
            const versionPath = passage.version ? `/${passage.version}` : '';
            const url = new URL(`/bible${versionPath}/${encodeURIComponent(passage.book)}/${passage.chapter}`, window.location.origin);
            
            if (passage.verses) {
                const start = passage.verses.split('-')[0];
                if (start) {
                    url.hash = start;
                }
            }
            return url.toString();
        }
        
        const url = new URL('/static/passage.html', window.location.origin);
        if (passage.source_path) {
            url.searchParams.set('path', passage.source_path);
        }
        if (passage.book) {
            url.searchParams.set('book', passage.book);
        }
        if (passage.chapter) {
            url.searchParams.set('chapter', passage.chapter);
        }
        if (passage.version) {
            url.searchParams.set('version', passage.version);
        }
        if (passage.reference) {
            url.searchParams.set('reference', passage.reference);
        }
        if (passage.verses) {
            const [start, end] = passage.verses.split('-');
            if (start) url.searchParams.set('start', start);
            if (end) url.searchParams.set('end', end);
        }
        return url.toString();
    }

    function buildFallbackReference(passage) {
        const book = passage.book || 'Book';
        const chapter = passage.chapter || '?';
        const verses = passage.verses || '?';
        return `${book} ${chapter}:${verses}`;
    }

    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
        } catch (err) {
            console.warn('Unable to copy text', err);
        }
    }

    function loadRecents() {
        try {
            const stored = localStorage.getItem(RECENT_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (err) {
            console.warn('Unable to load recents', err);
            return [];
        }
    }

    function persistRecentQuestion(question) {
        if (!question) return;
        const recents = loadRecents().filter(item => item.question !== question);
        recents.unshift({ question, ts: Date.now() });
        const trimmed = recents.slice(0, 8);
        try {
            localStorage.setItem(RECENT_KEY, JSON.stringify(trimmed));
            renderRecents(trimmed);
        } catch (err) {
            console.warn('Unable to save recents', err);
        }
    }

    function renderRecents(recents) {
        if (!recentList) return;
        recentList.innerHTML = '';
        if (!recents || recents.length === 0) {
            const empty = document.createElement('li');
            empty.className = 'recent-empty';
            empty.textContent = 'Ask something and we will keep it here for you.';
            recentList.appendChild(empty);
            return;
        }

        recents.forEach((item) => {
            const li = document.createElement('li');
            li.className = 'recent-item';

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'recent-question';
            button.textContent = item.question;
            button.addEventListener('click', () => {
                input.value = item.question;
                form.dispatchEvent(new Event('submit'));
            });

            const meta = document.createElement('span');
            meta.className = 'recent-meta';
            const date = new Date(item.ts || Date.now());
            meta.textContent = date.toLocaleString(undefined, { month: 'short', day: 'numeric' });

            li.appendChild(button);
            li.appendChild(meta);
            recentList.appendChild(li);
        });
    }

    function loadNotes() {
        if (!sessionNotes) return;
        try {
            const stored = localStorage.getItem(NOTES_KEY);
            if (stored !== null) {
                sessionNotes.value = stored;
                if (notesStatus) {
                    notesStatus.textContent = 'Saved locally';
                }
            }
        } catch (err) {
            console.warn('Unable to load notes', err);
        }
    }

    function persistNotes() {
        if (!sessionNotes) return;
        try {
            localStorage.setItem(NOTES_KEY, sessionNotes.value);
            if (notesStatus) {
                notesStatus.textContent = 'Saved just now';
            }
        } catch (err) {
            console.warn('Unable to save notes', err);
            if (notesStatus) {
                notesStatus.textContent = 'Could not save';
            }
        }
    }

    function copyAnswer() {
        if (!answerText) return;
        const plain = answerText.innerText.trim();
        if (!plain) return;
        copyToClipboard(plain);
        if (copyAnswerButton) {
            const original = copyAnswerButton.textContent;
            copyAnswerButton.textContent = 'Copied';
            setTimeout(() => {
                copyAnswerButton.textContent = original || 'Copy answer';
            }, 1800);
        }
    }

    async function refreshHealth() {
        if (!healthBadge || !healthDetail) {
            return;
        }
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            if (!response.ok) {
                throw new Error('Health check failed');
            }
            const ready = data.status === 'healthy' && data.rag_initialized;
            healthBadge.textContent = ready ? 'Ready' : 'Connecting';
            healthBadge.classList.toggle('is-healthy', ready);
            healthBadge.classList.toggle('is-warning', !ready);
            healthDetail.textContent = ready
                ? 'Scripture engine connected'
                : 'Connecting to Scripture database...';
        } catch (err) {
            healthBadge.textContent = 'Connecting';
            healthBadge.classList.add('is-warning');
            healthDetail.textContent = 'Connecting to Scripture database...';
        }
    }

    // Example questions for demonstration (optional)
    const exampleQuestions = [
        "What should I do when someone wrongs me?",
        "How should I treat my enemies?",
        "What does it mean to love my neighbor?",
        "How can I find peace in difficult times?",
        "What should I do when I am afraid?"
    ];

    // Add click handler for example questions (if you want to add them to UI later)
    window.askExample = function (question) {
        input.value = question;
        form.dispatchEvent(new Event('submit'));
    };

    // Bible reference hover preview system
    let activeTooltip = null;
    let tooltipTimeout = null;
    let currentRequest = null;
    let previewListenersAttached = false;

    // Mobile tap handling
    let lastTapTime = 0;
    let lastTappedLink = null;
    let touchHandled = false;
    const DOUBLE_TAP_DELAY = 300; // milliseconds

    function setupBibleRefHoverPreviews() {
        // Use event delegation on answerText container
        if (previewListenersAttached) return;
        answerText.addEventListener('mouseenter', handleBibleRefHover, true);
        answerText.addEventListener('mouseleave', handleBibleRefLeave, true);
        answerText.addEventListener('click', handleBibleRefClick, true);

        // Add touch event listeners for mobile
        answerText.addEventListener('touchstart', handleBibleRefTouchStart, true);
        answerText.addEventListener('touchend', handleBibleRefTouchEnd, true);
        previewListenersAttached = true;
    }

    function handleBibleRefHover(e) {
        const link = e.target.closest('.bible-ref-link');
        if (!link) return;

        e.preventDefault();

        // Clear any existing timeout
        clearTimeout(tooltipTimeout);

        // Delay showing tooltip slightly to avoid flashing on quick mouse movements
        tooltipTimeout = setTimeout(() => {
            showBibleTooltip(link);
        }, 200);
    }

    function handleBibleRefLeave(e) {
        const link = e.target.closest('.bible-ref-link');
        if (!link) return;

        clearTimeout(tooltipTimeout);

        // Delay hiding to allow moving mouse to tooltip
        tooltipTimeout = setTimeout(() => {
            hideTooltip();
        }, 300);
    }

    function handleBibleRefTouchStart(e) {
        const link = e.target.closest('.bible-ref-link');
        if (!link) return;

        e.preventDefault();
        e.stopPropagation();

        touchHandled = true;

        const currentTime = new Date().getTime();
        const timeSinceLastTap = currentTime - lastTapTime;

        // Check if this is a double tap on the same link
        if (timeSinceLastTap < DOUBLE_TAP_DELAY && lastTappedLink === link) {
            // Double tap - navigate to the passage
            handleBibleRefNavigate(link);

            // Reset tap tracking
            lastTapTime = 0;
            lastTappedLink = null;
            hideTooltip();
        } else {
            // Single tap - show the tooltip
            lastTapTime = currentTime;
            lastTappedLink = link;
            showBibleTooltip(link);
        }
    }

    function handleBibleRefTouchEnd(e) {
        // Reset touch flag after a delay to prevent click event
        setTimeout(() => {
            touchHandled = false;
        }, 400);
    }

    function handleBibleRefClick(e) {
        const link = e.target.closest('.bible-ref-link');
        if (!link) return;

        // Ignore click events that came from touch interactions
        if (touchHandled) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }

        e.preventDefault();

        // For mouse clicks, navigate immediately
        handleBibleRefNavigate(link);
    }

    function handleBibleRefNavigate(link) {
        // Build passage viewer URL and navigate
        const book = link.dataset.book;
        const chapter = link.dataset.chapter;
        const verseStart = link.dataset.verseStart;
        
        const url = new URL(`/bible/${encodeURIComponent(book)}/${chapter}`, window.location.origin);
        if (verseStart) {
            url.hash = verseStart;
        }

        window.open(url.toString(), '_blank', 'noopener,noreferrer');
    }

    async function showBibleTooltip(link) {
        const book = link.dataset.book;
        const chapter = link.dataset.chapter;
        const verseStart = link.dataset.verseStart;
        const verseEnd = link.dataset.verseEnd;

        // Create or reuse tooltip
        if (!activeTooltip) {
            activeTooltip = document.createElement('div');
            activeTooltip.className = 'bible-tooltip';
            document.body.appendChild(activeTooltip);

            // Keep tooltip visible when hovering over it
            activeTooltip.addEventListener('mouseenter', () => {
                clearTimeout(tooltipTimeout);
            });

            activeTooltip.addEventListener('mouseleave', () => {
                tooltipTimeout = setTimeout(() => {
                    hideTooltip();
                }, 200);
            });
        }

        // Position tooltip near the link
        const rect = link.getBoundingClientRect();
        activeTooltip.style.left = `${rect.left}px`;
        activeTooltip.style.top = `${rect.bottom + 8}px`;

        // Show loading state
        activeTooltip.innerHTML = '<div class="tooltip-loading">Loading verse...</div>';
        activeTooltip.classList.add('visible');

        // Cancel any pending request
        if (currentRequest) {
            currentRequest.abort();
        }

        // Fetch verse text
        try {
            const controller = new AbortController();
            currentRequest = controller;

            const url = new URL('/api/verse-preview', window.location.origin);
            url.searchParams.set('book', book);
            url.searchParams.set('chapter', chapter);
            url.searchParams.set('verse_start', verseStart);
            url.searchParams.set('verse_end', verseEnd);

            const response = await fetch(url, { signal: controller.signal });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load verse');
            }

            // Update tooltip content
            const reference = `${book} ${chapter}:${verseStart}${verseEnd !== verseStart ? '-' + verseEnd : ''}`;
            const isMobile = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            const hintText = isMobile ? 'Double tap to view full chapter' : 'Click to view full chapter';

            activeTooltip.innerHTML = `
                <div class="tooltip-reference">${reference}</div>
                <div class="tooltip-text">${data.text}</div>
                <div class="tooltip-hint">${hintText}</div>
            `;

            // Adjust position if tooltip goes off-screen
            const tooltipRect = activeTooltip.getBoundingClientRect();
            if (tooltipRect.right > window.innerWidth) {
                activeTooltip.style.left = `${window.innerWidth - tooltipRect.width - 10}px`;
            }
            if (tooltipRect.left < 0) {
                activeTooltip.style.left = '10px';
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                return; // Request was cancelled
            }
            console.error('Error fetching verse preview:', error);

            // Show more helpful error message
            const reference = `${book} ${chapter}:${verseStart}${verseEnd !== verseStart ? '-' + verseEnd : ''}`;
            const errorMessage = error.message.includes('not found')
                ? `Verse ${reference} does not exist in this chapter.`
                : 'Failed to load verse preview.';

            activeTooltip.innerHTML = `
                <div class="tooltip-reference">${reference}</div>
                <div class="tooltip-error">${errorMessage}</div>
                <div class="tooltip-hint">Click to view the full chapter</div>
            `;
        } finally {
            currentRequest = null;
        }
    }

    function hideTooltip() {
        if (activeTooltip) {
            activeTooltip.classList.remove('visible');
        }
    }

    if (copyAnswerButton) {
        copyAnswerButton.addEventListener('click', copyAnswer);
    }
    
    if (listenButton) {
        listenButton.addEventListener('click', () => {
            if (!answerText) return;

            if (document.body.classList.contains('paperwhite-mode')) {
                if (window.speechSynthesis && window.speechSynthesis.speaking) {
                    window.speechSynthesis.cancel();
                }
                listenButton.textContent = 'Listen 🔊';
                return;
            }

            if (window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
                listenButton.textContent = 'Listen 🔊';
                return;
            }

            // Get plain text from the answer
            const textToSpeak = answerText.innerText;
            if (!textToSpeak) return;

            const utterance = new SpeechSynthesisUtterance(textToSpeak);

            // Try to select a good voice
            const voices = window.speechSynthesis.getVoices();
            // Prefer Google US English or similar natural sounding voice
            const preferredVoice = voices.find(v => v.name.includes('Google US English')) ||
                                 voices.find(v => v.lang === 'en-US') ||
                                 voices[0];
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            utterance.onstart = () => {
                listenButton.textContent = 'Stop ⏹';
            };

            utterance.onend = () => {
                listenButton.textContent = 'Listen 🔊';
            };

            utterance.onerror = () => {
                listenButton.textContent = 'Listen 🔊';
            };

            window.speechSynthesis.speak(utterance);
        });
    }

    if (shareAnswerButton) {
        shareAnswerButton.addEventListener('click', async () => {
            if (!lastResponseData) return;
            
            const originalText = shareAnswerButton.textContent;
            shareAnswerButton.textContent = 'Saving...';
            shareAnswerButton.disabled = true;
            
            try {
                const response = await fetch('/api/share', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(lastResponseData)
                });
                
                if (!response.ok) throw new Error('Failed to share');
                
                const data = await response.json();
                await copyToClipboard(data.share_url);
                
                shareAnswerButton.textContent = 'Copied Link!';
                setTimeout(() => {
                    shareAnswerButton.textContent = originalText;
                    shareAnswerButton.disabled = false;
                }, 2000);
                
            } catch (error) {
                console.error('Share error:', error);
                shareAnswerButton.textContent = 'Error';
                setTimeout(() => {
                    shareAnswerButton.textContent = originalText;
                    shareAnswerButton.disabled = false;
                }, 2000);
            }
        });
    }

    if (clearRecentsButton) {
        clearRecentsButton.addEventListener('click', () => {
            localStorage.removeItem(RECENT_KEY);
            renderRecents([]);
        });
    }
    if (sessionNotes) {
        sessionNotes.addEventListener('input', () => {
            if (notesStatus) {
                notesStatus.textContent = 'Unsaved';
            }
        });
    }
    if (saveNotesButton) {
        saveNotesButton.addEventListener('click', persistNotes);
    }

    renderRecents(loadRecents());
    loadNotes();
    // Version Dropdown Logic
    const versionDropdown = document.getElementById('versionDropdown');
    const versionBtn = document.getElementById('versionBtn');
    const versionMenu = document.getElementById('versionMenu');
    const currentVersionDisplay = document.getElementById('currentVersionDisplay');
    const versionInput = document.getElementById('versionSelector');

    if (versionBtn) {
        versionBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            versionDropdown.classList.toggle('open');
        });
    }

    document.addEventListener('click', (e) => {
        if (versionDropdown && versionDropdown.classList.contains('open') && !versionDropdown.contains(e.target)) {
            versionDropdown.classList.remove('open');
        }
    });

    loadVersions();
    refreshHealth();
    updateModeUI();
    autoResizeInput();

    // Load available Bible versions from API (KISS - single source of truth)
    async function loadVersions() {
        if (!versionMenu) return;
        try {
            const response = await fetch('/api/versions');
            const data = await response.json();
            if (data.versions && data.versions.length > 0) {
                versionMenu.innerHTML = '';
                const currentVer = versionInput ? versionInput.value : 'kjv';
                
                let foundCurrent = false;

                data.versions.forEach(v => {
                    const option = document.createElement('div');
                    option.className = 'version-option';
                    if (v.code === currentVer) {
                        option.classList.add('active');
                        if (currentVersionDisplay) currentVersionDisplay.textContent = v.short;
                        foundCurrent = true;
                    }
                    
                    option.innerHTML = `
                        <span class="version-code">${v.short}</span>
                        <span class="version-name">${v.name}</span>
                    `;
                    
                    option.addEventListener('click', () => {
                        // Update active state
                        document.querySelectorAll('.version-option').forEach(el => el.classList.remove('active'));
                        option.classList.add('active');
                        
                        if (versionInput) versionInput.value = v.code;
                        if (currentVersionDisplay) currentVersionDisplay.textContent = v.short;
                        
                        versionDropdown.classList.remove('open');
                    });
                    
                    versionMenu.appendChild(option);
                });
                
                if (!foundCurrent && data.versions.length > 0) {
                    if (currentVersionDisplay) currentVersionDisplay.textContent = data.versions[0].short;
                    if (versionInput) versionInput.value = data.versions[0].code;
                }
            }
        } catch (err) {
            console.warn('Could not load versions:', err);
        }
    }

    // Header & Mobile Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const sections = {
        '#top': document.body,
        '#study-cta': document.getElementById('study-cta'),
        '#study-tools': document.getElementById('study-tools'),
        '#about': document.getElementById('about')
    };

    function updateActiveNav() {
        // Only manage active state dynamically for anchor links starting with '#'
        const anchorNavItems = Array.from(navItems).filter(item => {
            const href = item.getAttribute('href');
            return href && href.startsWith('#');
        });

        if (anchorNavItems.length === 0) return;

        let current = '';
        const scrollPosition = window.scrollY + window.innerHeight / 3;

        for (const [id, section] of Object.entries(sections)) {
            if (section && section.offsetTop <= scrollPosition) {
                current = id;
            }
        }

        if (window.scrollY < 100) current = '#top';

        anchorNavItems.forEach(item => {
            if (item.getAttribute('href') === current) {
                item.classList.add('is-active');
            } else {
                item.classList.remove('is-active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveNav);
    
    // Initial check
    updateActiveNav();

    // Handle nav clicks for smooth scrolling ONLY on anchor links starting with '#'
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const targetId = item.getAttribute('href');
            if (!targetId) return;

            // Only prevent default and smooth scroll if it's an anchor link (#)
            if (targetId.startsWith('#')) {
                const targetSection = sections[targetId];
                if (targetSection) {
                    e.preventDefault();
                    if (targetId === '#top') {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    } else {
                        targetSection.scrollIntoView({ behavior: 'smooth' });
                    }
                    
                    if (targetId === '#study-cta' && input) {
                        setTimeout(() => {
                            input.focus();
                        }, 500);
                    }
                }
            }
            // For normal page links like '/', '/bible', '/devotional', '/prayers', '/plans', '/topics',
            // do NOT call e.preventDefault(); let normal browser navigation occur.
        });
    });

    // Collapsible Hero Logic
    const heroSection = document.querySelector('.primary-hero');
    
    if (heroSection) {
        input.addEventListener('focus', () => {
            // On mobile, collapse the hero to save space when typing
            if (window.innerWidth <= 640) {
                heroSection.classList.add('collapsed');
            }
        });
    }

    // ========================================
    // Verse of the Day Feature
    // ========================================
    loadVerseOfTheDay();
    loadCommunityQuestions();

    async function loadCommunityQuestions() {
        const container = document.getElementById('communityQuestions');
        const list = document.getElementById('communityQuestionsList');

        // Only fetch if not already populated by SSR
        if (!container || !list || list.children.length > 0) return;

        try {
            const response = await fetch('/api/recent-shares?limit=6');
            if (!response.ok) return;

            const data = await response.json();
            const shares = data.shares || [];

            if (shares.length === 0) return;

            list.innerHTML = '';
            shares.forEach(share => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'question-pill';
                button.textContent = share.question.length > 50 ? share.question.substring(0, 50) + '...' : share.question;
                button.title = share.question;

                button.addEventListener('click', () => {
                   window.location.href = `/q/${share.id}`;
                });

                list.appendChild(button);
            });

            container.style.display = 'block';
        } catch (err) {
            console.warn('Could not load community questions:', err);
        }
    }

    async function loadVerseOfTheDay() {
        const container = document.getElementById('verseOfTheDay');
        const textEl = document.getElementById('vodText');
        const refEl = document.getElementById('vodRef');
        const compareBtn = document.getElementById('vodCompare');
        
        if (!container || !textEl || !refEl) return;
        
        try {
            const version = document.getElementById('versionSelector')?.value || 'kjv';
            const response = await fetch(`/api/random-verse?version=${version}`);
            const data = await response.json();
            
            textEl.textContent = `"${data.text}"`;
            refEl.textContent = `— ${data.reference} (${data.version})`;
            container.style.display = 'block';
            
            // Store verse data for comparison
            container.dataset.book = data.book;
            container.dataset.chapter = data.chapter;
            container.dataset.verse = data.verse;
            
            if (compareBtn) {
                compareBtn.addEventListener('click', () => {
                    showCompareModal(data.book, data.chapter, data.verse, data.reference);
                });
            }
        } catch (err) {
            console.warn('Could not load verse of the day:', err);
        }
    }

    async function showCompareModal(book, chapter, verse, reference) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'compare-modal';
        modal.innerHTML = `
            <div class="compare-modal-content">
                <div class="compare-modal-header">
                    <h3 class="compare-modal-title">${reference} - Compare Translations</h3>
                    <button class="compare-modal-close" aria-label="Close">&times;</button>
                </div>
                <div class="compare-modal-body">
                    <p style="color: var(--text-muted);">Loading translations...</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close handlers
        modal.querySelector('.compare-modal-close').addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        // Fetch comparisons
        try {
            const response = await fetch(`/api/compare-verse?book=${encodeURIComponent(book)}&chapter=${chapter}&verse=${verse}`);
            const data = await response.json();
            
            const bodyEl = modal.querySelector('.compare-modal-body');
            if (data.comparisons && data.comparisons.length > 0) {
                bodyEl.innerHTML = data.comparisons.map(c => `
                    <div class="compare-item">
                        <div class="compare-version">${c.version_name}</div>
                        <div class="compare-text">${c.text}</div>
                    </div>
                `).join('');
            } else {
                bodyEl.innerHTML = '<p style="color: var(--text-muted);">No translations available for comparison.</p>';
            }
        } catch (err) {
            modal.querySelector('.compare-modal-body').innerHTML = '<p style="color: var(--danger);">Failed to load translations.</p>';
        }
    }

    // ========================================
    // Keyboard Shortcuts
    // ========================================
    document.addEventListener('keydown', (e) => {
        // Don't trigger shortcuts when typing in input fields
        if (e.target.matches('input, textarea, select')) return;
        
        // Ctrl/Cmd + K: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            input.focus();
        }
        
        // Escape: Clear input or close modal
        if (e.key === 'Escape') {
            const modal = document.querySelector('.compare-modal');
            if (modal) {
                modal.remove();
            } else if (document.activeElement === input) {
                input.blur();
            }
        }
        
        // Number keys 1-5: Switch modes (when not typing)
        if (['1', '2', '3', '4', '5'].includes(e.key) && !e.ctrlKey && !e.metaKey && !e.altKey) {
            const modes = ['balanced', 'comfort', 'clarity', 'challenge', 'blessing'];
            const modeIndex = parseInt(e.key) - 1;
            if (modes[modeIndex]) {
                setMode(modes[modeIndex]);
            }
        }
        
        // B: Open Bible reader
        if (e.key === 'b' && !e.ctrlKey && !e.metaKey) {
            window.location.href = '/bible';
        }
    });

    // Auto-trigger question from URL query parameter (e.g. ?q=... or ?question=...)
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const urlQuery = urlParams.get('q') || urlParams.get('question') || urlParams.get('query');
        const initialQuery = urlQuery || (input ? input.value : '');
        if (initialQuery) {
            const trimmedQuery = initialQuery.trim();
            if (trimmedQuery && input && form) {
                if (currentTool !== 'ask') {
                    switchTool('ask');
                }
                input.value = trimmedQuery;
                autoResizeInput();
                setTimeout(() => {
                    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }, 150);
            }
        }
    } catch (queryErr) {
        console.warn('Could not parse query param:', queryErr);
    }
});
