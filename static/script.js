// Main application logic
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const input = document.getElementById('questionInput');
    const askButton = document.getElementById('askButton');
    const buttonText = document.getElementById('buttonText');
    const buttonSpinner = document.getElementById('buttonSpinner');
    
    const responseSection = document.getElementById('responseSection');
    const answerText = document.getElementById('answerText');
    const passagesContainer = document.getElementById('passagesContainer');
    
    const errorSection = document.getElementById('errorSection');
    const errorText = document.getElementById('errorText');
    
    const loadingSection = document.getElementById('loadingSection');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const question = input.value.trim();
        if (!question) return;

        // Show loading state
        showLoading();
        hideResponse();
        hideError();

        try {
            // Use streaming endpoint
            await askQuestionStream(question);

        } catch (error) {
            console.error('Error:', error);
            displayError(error.message || 'An error occurred while processing your request. Please try again.');
            hideLoading();
        }
    });

    async function askQuestionStream(question) {
        // Handle streaming response from the server
        const response = await fetch('/api/ask-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to get response');
        }

        // Set up EventSource-like handling for SSE
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let accumulatedAnswer = '';
        let passages = [];

        // Show response section immediately
        answerText.innerHTML = '<span class="typing-cursor"></span>';
        responseSection.style.display = 'block';
        hideLoading();

        // Scroll to response
        setTimeout(() => {
            responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // Process complete SSE messages
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete message in buffer
            
            for (const line of lines) {
                if (!line.trim()) continue;
                
                // Parse SSE format: "event: eventname\ndata: jsondata"
                const eventMatch = line.match(/event: (\w+)\ndata: (.+)/s);
                if (!eventMatch) continue;
                
                const [, eventType, jsonData] = eventMatch;
                const data = JSON.parse(jsonData);
                
                if (eventType === 'passages') {
                    // Store passages to display later
                    passages = data.passages;
                } else if (eventType === 'chunk') {
                    // Append text chunk
                    accumulatedAnswer += data.text;
                    answerText.innerHTML = renderMarkdown(accumulatedAnswer) + '<span class="typing-cursor"></span>';
                    setupBibleRefHoverPreviews();
                } else if (eventType === 'done') {
                    // Remove typing cursor
                    answerText.innerHTML = renderMarkdown(accumulatedAnswer);
                    setupBibleRefHoverPreviews();
                    
                    // Display passages
                    displayPassages(passages);
                } else if (eventType === 'error') {
                    throw new Error(data.error);
                }
            }
        }
    }

    function displayPassages(passages) {
        // Display Bible passages in the UI
        passagesContainer.innerHTML = '';
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
                meta.textContent = metaParts.join(' • ');
                
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
                if (metaParts.length) {
                    passageDiv.appendChild(meta);
                }
                passageDiv.appendChild(text);
                passageDiv.appendChild(actions);
                passagesContainer.appendChild(passageDiv);
            });
        }
    }

    function showLoading() {
        loadingSection.style.display = 'block';
        askButton.disabled = true;
        buttonText.style.display = 'none';
        buttonSpinner.style.display = 'inline';
    }

    function hideLoading() {
        loadingSection.style.display = 'none';
        askButton.disabled = false;
        buttonText.style.display = 'inline';
        buttonSpinner.style.display = 'none';
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
                meta.textContent = metaParts.join(' • ');
                
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
                if (metaParts.length) {
                    passageDiv.appendChild(meta);
                }
                passageDiv.appendChild(text);
                passageDiv.appendChild(actions);
                passagesContainer.appendChild(passageDiv);
            });
        }

        responseSection.style.display = 'block';
        
        // Smooth scroll to response
        setTimeout(() => {
            responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    function hideResponse() {
        responseSection.style.display = 'none';
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
        const bibleRefPattern = /(\d?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(\d+):(\d+)(?:-(\d+))?/g;
        
        return html.replace(bibleRefPattern, (match, book, chapter, verseStart, verseEnd) => {
            const reference = `${book.trim()} ${chapter}:${verseStart}${verseEnd ? '-' + verseEnd : ''}`;
            const dataAttrs = `data-book="${book.trim()}" data-chapter="${chapter}" data-verse-start="${verseStart}" data-verse-end="${verseEnd || verseStart}"`;
            return `<a href="#" class="bible-ref-link" ${dataAttrs} title="${reference}">${reference}</a>`;
        });
    }

    function buildPassageViewerUrl(passage) {
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

    // Example questions for demonstration (optional)
    const exampleQuestions = [
        "What should I do when someone wrongs me?",
        "How should I treat my enemies?",
        "What does it mean to love my neighbor?",
        "How can I find peace in difficult times?",
        "What should I do when I am afraid?"
    ];

    // Add click handler for example questions (if you want to add them to UI later)
    window.askExample = function(question) {
        input.value = question;
        form.dispatchEvent(new Event('submit'));
    };

    // Bible reference hover preview system
    let activeTooltip = null;
    let tooltipTimeout = null;
    let currentRequest = null;

    function setupBibleRefHoverPreviews() {
        // Use event delegation on answerText container
        answerText.addEventListener('mouseenter', handleBibleRefHover, true);
        answerText.addEventListener('mouseleave', handleBibleRefLeave, true);
        answerText.addEventListener('click', handleBibleRefClick, true);
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

    function handleBibleRefClick(e) {
        const link = e.target.closest('.bible-ref-link');
        if (!link) return;

        e.preventDefault();
        
        // Build passage viewer URL
        const book = link.dataset.book;
        const chapter = link.dataset.chapter;
        const verseStart = link.dataset.verseStart;
        const verseEnd = link.dataset.verseEnd;
        
        const url = new URL('/static/passage.html', window.location.origin);
        url.searchParams.set('book', book);
        url.searchParams.set('chapter', chapter);
        url.searchParams.set('start', verseStart);
        url.searchParams.set('end', verseEnd);
        
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
            activeTooltip.innerHTML = `
                <div class="tooltip-reference">${reference}</div>
                <div class="tooltip-text">${data.text}</div>
                <div class="tooltip-hint">Click to view full chapter</div>
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
            activeTooltip.innerHTML = '<div class="tooltip-error">Failed to load verse</div>';
        } finally {
            currentRequest = null;
        }
    }

    function hideTooltip() {
        if (activeTooltip) {
            activeTooltip.classList.remove('visible');
        }
    }

    initHolyTrinityEasterEgg();
    initInteractiveBackground();

    function initHolyTrinityEasterEgg() {
        const state = {
            overlay: null,
            hideTimeoutId: null
        };

        input.addEventListener('input', () => {
            if (containsHolyTrinity(input.value)) {
                triggerHolyTrinity();
            }
        });

        function containsHolyTrinity(value) {
            if (!value) {
                return false;
            }
            const normalized = value.toLowerCase();
            const hasFather = normalized.includes('father');
            const hasSon = normalized.includes('son');
            const hasSpirit =
                normalized.includes('holy spirit') ||
                normalized.includes('holy-spirit') ||
                normalized.includes('holyspirit');
            return hasFather && hasSon && hasSpirit;
        }

        function triggerHolyTrinity() {
            const overlay = ensureOverlay();
            overlay.classList.add('visible');
            document.body.classList.add('holy-trinity-active');

            clearTimeout(state.hideTimeoutId);
            state.hideTimeoutId = setTimeout(() => {
                overlay.classList.remove('visible');
                document.body.classList.remove('holy-trinity-active');
            }, 5000);
        }

        function ensureOverlay() {
            if (state.overlay) {
                return state.overlay;
            }
            const overlay = document.createElement('div');
            overlay.className = 'trinity-overlay';
            overlay.setAttribute('aria-hidden', 'true');
            overlay.innerHTML = `
                <div class="trinity-cluster">
                    <div class="trinity-glow"></div>
                    <div class="trinity-ring"></div>
                    <div class="trinity-orb orb-father">Father</div>
                    <div class="trinity-orb orb-son">Son</div>
                    <div class="trinity-orb orb-spirit">Spirit</div>
                    <div class="trinity-cross"></div>
                </div>
                <p class="trinity-whisper">Father • Son • Holy Spirit</p>
            `;
            document.body.appendChild(overlay);
            state.overlay = overlay;
            return overlay;
        }
    }

    function initInteractiveBackground() {
        const root = document.documentElement;
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        let rafId = null;
        let pointerX = 50;
        let pointerY = 40;
        let motionEnabled = false;

        const commitPointer = () => {
            root.style.setProperty('--pointer-x', `${pointerX}%`);
            root.style.setProperty('--pointer-y', `${pointerY}%`);
            rafId = null;
        };

        const scheduleCommit = () => {
            if (rafId === null) {
                rafId = requestAnimationFrame(commitPointer);
            }
        };

        const clamp = (value) => Math.min(100, Math.max(0, value));

        const handlePointerMove = (event) => {
            pointerX = clamp((event.clientX / window.innerWidth) * 100);
            pointerY = clamp((event.clientY / window.innerHeight) * 100);
            scheduleCommit();
        };

        const handlePointerLeave = () => {
            pointerX = 50;
            pointerY = 40;
            scheduleCommit();
        };

        const enableMotion = () => {
            if (motionEnabled) return;
            motionEnabled = true;
            scheduleCommit();
            document.addEventListener('pointermove', handlePointerMove);
            document.addEventListener('pointerleave', handlePointerLeave);
        };

        const disableMotion = () => {
            if (!motionEnabled) return;
            motionEnabled = false;
            document.removeEventListener('pointermove', handlePointerMove);
            document.removeEventListener('pointerleave', handlePointerLeave);
            handlePointerLeave();
        };

        const motionChangeHandler = (event) => {
            if (event.matches) {
                disableMotion();
            } else {
                enableMotion();
            }
        };

        scheduleCommit();

        if (motionQuery.matches) {
            disableMotion();
        } else {
            enableMotion();
        }

        if (typeof motionQuery.addEventListener === 'function') {
            motionQuery.addEventListener('change', motionChangeHandler);
        } else if (typeof motionQuery.addListener === 'function') {
            motionQuery.addListener(motionChangeHandler);
        }
    }
});
