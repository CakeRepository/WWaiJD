document.addEventListener('DOMContentLoaded', () => {
    const libraryContainer = document.getElementById('libraryContainer');
    const chapterTitle = document.getElementById('chapterTitle');
    const chapterSubtitle = document.getElementById('chapterSubtitle');
    const chapterBody = document.getElementById('chapterBody');
    const chapterLoading = document.getElementById('chapterLoading');
    const chapterError = document.getElementById('chapterError');
    const openStandalone = document.getElementById('openStandalone');
    const nightModeToggle = document.getElementById('nightModeToggle');
    const chapterNav = document.getElementById('chapterNav');
    const prevChapter = document.getElementById('prevChapter');
    const nextChapter = document.getElementById('nextChapter');
    const coffeeMargin = document.getElementById('coffeeMargin');
    const coffeeVerse = document.getElementById('coffeeVerse');
    const coffeeSubtext = document.getElementById('coffeeSubtext');
    
    // Version Selector Elements
    const versionDropdown = document.getElementById('versionDropdown');
    const versionBtn = document.getElementById('versionBtn');
    const versionMenu = document.getElementById('versionMenu');
    const currentVersionDisplay = document.getElementById('currentVersionDisplay');

    let activeButton = null;
    let currentPassageMeta = null;
    let isNightMode = localStorage.getItem('nightMode') === 'true';
    let bibleIndex = null; // Store the full Bible index for navigation
    const coffeeMarginNotes = [
        {
            reference: 'Proverbs 11:25',
            text: 'The liberal soul shall be made fat; he that watereth shall be watered also himself.'
        },
        {
            reference: 'Hebrews 13:16',
            text: 'But to do good and to communicate forget not: for with such sacrifices God is well pleased.'
        },
        {
            reference: 'Luke 6:38',
            text: 'Give, and it shall be given unto you; good measure, pressed down, and shaken together.'
        },
        {
            reference: 'Romans 12:13',
            text: 'Distributing to the necessity of saints; given to hospitality.'
        }
    ];
    let lastCoffeeNoteIndex = -1;
    
    // Reading history
    const HISTORY_KEY = 'wwaijd:reading-history';
    const MAX_HISTORY = 10;

    // Initialize night mode
    if (isNightMode) {
        document.body.classList.add('night-mode');
        nightModeToggle.textContent = '🌙 Night Mode';
    }

    // Night mode toggle
    nightModeToggle.addEventListener('click', () => {
        isNightMode = !isNightMode;
        document.body.classList.toggle('night-mode');
        nightModeToggle.textContent = isNightMode ? '🌙 Night Mode' : '☀️ Day Mode';
        localStorage.setItem('nightMode', isNightMode);
    });

    // Navigation buttons
    prevChapter.addEventListener('click', () => navigateChapter(-1));
    nextChapter.addEventListener('click', () => navigateChapter(1));

    // Helper to get current version
    function getCurrentVersion() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('version') || 'kjv';
    }

    // Helper to set version
    function setVersion(version, name, short) {
        currentVersionDisplay.textContent = short.toUpperCase();
        
        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('version', version);
        window.history.pushState({}, '', url);
        
        // Refresh library
        fetchLibrary();
        
        // Clear current chapter view
        chapterBody.innerHTML = '';
        chapterTitle.textContent = 'Select a Passage';
        chapterSubtitle.textContent = 'Choose any book or chapter from the library to begin your journey.';
        currentPassageMeta = null;
        toggleStandalone(null, false);
    }

    // Toggle Dropdown
    if (versionBtn) {
        versionBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            versionDropdown.classList.toggle('open');
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (versionDropdown && versionDropdown.classList.contains('open') && !versionDropdown.contains(e.target)) {
            versionDropdown.classList.remove('open');
        }
    });

    // Load available versions from API
    loadVersions();
    fetchLibrary();
    refreshCoffeeMargin(null);
    
    // Check for resume reading
    checkResumeReading();

    async function loadVersions() {
        if (!versionMenu) return;
        try {
            const response = await fetch('/api/versions');
            const data = await response.json();
            if (data.versions && data.versions.length > 0) {
                versionMenu.innerHTML = '';
                const currentVer = getCurrentVersion();
                
                let foundCurrent = false;

                data.versions.forEach(v => {
                    const option = document.createElement('div');
                    option.className = 'version-option';
                    if (v.code === currentVer) {
                        option.classList.add('active');
                        currentVersionDisplay.textContent = v.short;
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
                        
                        setVersion(v.code, v.name, v.short);
                        versionDropdown.classList.remove('open');
                    });
                    
                    versionMenu.appendChild(option);
                });
                
                if (!foundCurrent && data.versions.length > 0) {
                    // If current version not found, default to first
                    currentVersionDisplay.textContent = data.versions[0].short;
                }
            }
        } catch (err) {
            console.warn('Could not load versions:', err);
        }
    }

    async function fetchLibrary() {
        try {
            const version = getCurrentVersion();
            const response = await fetch(`/api/bible-index?version=${version}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unable to load library.');
            }

            bibleIndex = data.testaments || [];
            renderLibrary(bibleIndex);
        } catch (err) {
            libraryContainer.innerHTML = `<div class="panel-empty">${err.message}</div>`;
        }
    }

    function renderLibrary(testaments) {
        if (!testaments.length) {
            libraryContainer.innerHTML = '<div class="panel-empty">No books found.</div>';
            return;
        }

        libraryContainer.innerHTML = '';
        testaments.forEach(testament => {
            const testamentSection = document.createElement('section');
            testamentSection.className = 'testament';

            const title = document.createElement('h3');
            title.textContent = testament.name;
            testamentSection.appendChild(title);

            testament.books.forEach(book => {
                const details = document.createElement('details');
                details.className = 'book-card';

                const summary = document.createElement('summary');
                summary.textContent = book.name;
                const chevron = document.createElement('span');
                chevron.textContent = 'v';
                summary.appendChild(chevron);
                details.appendChild(summary);

                const chapterGrid = document.createElement('div');
                chapterGrid.className = 'chapter-grid';

                book.chapters.forEach(chapter => {
                    const button = document.createElement('button');
                    button.className = 'chapter-chip';
                    button.type = 'button';
                    button.textContent = chapter.number;
                    button.addEventListener('click', () => {
                        setActiveButton(button);
                        loadChapter({
                            book: book.name,
                            testament: testament.name,
                            chapter: chapter.number,
                            path: chapter.path,
                        });
                        
                        // Scroll chapter panel to top when loading new chapter
                        chapterBody.scrollTop = 0;
                        
                        // Smooth scroll button into view in library panel
                        button.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    });

                    chapterGrid.appendChild(button);
                });

                details.appendChild(chapterGrid);
                testamentSection.appendChild(details);
            });

            libraryContainer.appendChild(testamentSection);
        });
    }

    function setActiveButton(button) {
        if (activeButton) {
            activeButton.classList.remove('active');
        }
        activeButton = button;
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }

    async function loadChapter(meta) {
        currentPassageMeta = meta;
        toggleStandalone(meta, false);

        chapterError.hidden = true;
        chapterBody.innerHTML = '';
        chapterLoading.hidden = false;

        chapterTitle.textContent = `${meta.book} ${meta.chapter}`;
        chapterSubtitle.textContent = meta.testament;

        const url = new URL('/api/bible-passage', window.location.origin);
        url.searchParams.set('path', meta.path);

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unable to load chapter.');
            }

            renderChapter(data);
            saveToHistory(meta);  // Save to reading history
        } catch (err) {
            showChapterError(err.message);
        } finally {
            chapterLoading.hidden = true;
        }
    }

    function renderChapter(data) {
        const verses = data.verses || [];
        if (!verses.length) {
            chapterBody.innerHTML = '<div class="panel-empty">We could not parse this chapter.</div>';
        } else {
            const fragment = document.createDocumentFragment();
            verses.forEach(verse => {
                const row = document.createElement('div');
                row.className = 'verse-row';

                const number = document.createElement('div');
                number.className = 'verse-number';
                number.textContent = verse.number;

                const text = document.createElement('div');
                text.className = 'verse-text';
                text.textContent = verse.text;

                row.appendChild(number);
                row.appendChild(text);
                fragment.appendChild(row);
            });
            chapterBody.innerHTML = '';
            chapterBody.appendChild(fragment);
        }

        toggleStandalone(data, true);
        updateNavigationButtons();
        refreshCoffeeMargin(currentPassageMeta);
    }

    function showChapterError(message) {
        chapterError.textContent = message;
        chapterError.hidden = false;
    }

    function refreshCoffeeMargin(meta) {
        if (!coffeeMargin || !coffeeVerse || !coffeeMarginNotes.length) {
            return;
        }

        let noteIndex = Math.floor(Math.random() * coffeeMarginNotes.length);
        if (coffeeMarginNotes.length > 1 && noteIndex === lastCoffeeNoteIndex) {
            noteIndex = (noteIndex + 1) % coffeeMarginNotes.length;
        }
        lastCoffeeNoteIndex = noteIndex;

        const note = coffeeMarginNotes[noteIndex];
        coffeeVerse.innerHTML = `<strong>${note.reference}</strong> ${note.text}`;

        if (coffeeSubtext) {
            if (meta && meta.book) {
                coffeeSubtext.textContent = `If today's time in ${meta.book} ${meta.chapter} refreshed you, pass the cup to keep this Bible free for everyone.`;
            } else {
                coffeeSubtext.textContent = 'If these readings steady you, pass the cup to help keep this Bible free for everyone.';
            }
        }

        coffeeMargin.hidden = false;
    }

    function toggleStandalone(data, enable) {
        if (!enable) {
            openStandalone.disabled = true;
            openStandalone.onclick = null;
            return;
        }

        const meta = currentPassageMeta || {};
        openStandalone.disabled = false;
        openStandalone.onclick = () => {
            const book = meta.book || data.book;
            const chapter = meta.chapter || data.chapter;
            const version = getCurrentVersion();
            // Use new SSR route
            const readerUrl = new URL(`/bible/${version}/${encodeURIComponent(book)}/${chapter}`, window.location.origin);
            window.open(readerUrl.toString(), '_blank', 'noopener');
        };
    }

    function navigateChapter(direction) {
        if (!currentPassageMeta || !bibleIndex) return;

        const { testament, book, chapter } = currentPassageMeta;
        
        // Find current position in the index
        let foundTestament = null;
        let foundBook = null;
        let foundChapterIndex = -1;

        for (const t of bibleIndex) {
            if (t.name === testament) {
                foundTestament = t;
                for (const b of t.books) {
                    if (b.name === book) {
                        foundBook = b;
                        foundChapterIndex = b.chapters.findIndex(c => c.number === chapter);
                        break;
                    }
                }
                break;
            }
        }

        if (!foundBook || foundChapterIndex === -1) return;

        let nextChapterData = null;

        if (direction === 1) {
            // Next chapter
            if (foundChapterIndex < foundBook.chapters.length - 1) {
                // Next chapter in same book
                nextChapterData = foundBook.chapters[foundChapterIndex + 1];
            } else {
                // First chapter of next book
                const bookIndex = foundTestament.books.findIndex(b => b.name === book);
                if (bookIndex < foundTestament.books.length - 1) {
                    const nextBook = foundTestament.books[bookIndex + 1];
                    nextChapterData = nextBook.chapters[0];
                } else {
                    // Try first book of next testament
                    const testamentIndex = bibleIndex.findIndex(t => t.name === testament);
                    if (testamentIndex < bibleIndex.length - 1) {
                        const nextTestament = bibleIndex[testamentIndex + 1];
                        const nextBook = nextTestament.books[0];
                        nextChapterData = nextBook.chapters[0];
                    }
                }
            }
        } else if (direction === -1) {
            // Previous chapter
            if (foundChapterIndex > 0) {
                // Previous chapter in same book
                nextChapterData = foundBook.chapters[foundChapterIndex - 1];
            } else {
                // Last chapter of previous book
                const bookIndex = foundTestament.books.findIndex(b => b.name === book);
                if (bookIndex > 0) {
                    const prevBook = foundTestament.books[bookIndex - 1];
                    nextChapterData = prevBook.chapters[prevBook.chapters.length - 1];
                } else {
                    // Try last book of previous testament
                    const testamentIndex = bibleIndex.findIndex(t => t.name === testament);
                    if (testamentIndex > 0) {
                        const prevTestament = bibleIndex[testamentIndex - 1];
                        const prevBook = prevTestament.books[prevTestament.books.length - 1];
                        nextChapterData = prevBook.chapters[prevBook.chapters.length - 1];
                    }
                }
            }
        }

        if (nextChapterData) {
            // Find and activate the button for the next chapter
            const buttons = document.querySelectorAll('.chapter-chip');
            for (const btn of buttons) {
                if (btn.textContent === nextChapterData.number) {
                    // Check if this button belongs to the correct book by looking at parent structure
                    const bookCard = btn.closest('.book-card');
                    if (bookCard) {
                        const summary = bookCard.querySelector('summary');
                        if (summary && summary.textContent.includes(getBookNameFromPath(nextChapterData.path))) {
                            setActiveButton(btn);
                            loadChapter({
                                book: getBookNameFromPath(nextChapterData.path),
                                testament: getTestamentFromPath(nextChapterData.path),
                                chapter: nextChapterData.number,
                                path: nextChapterData.path,
                            });
                            
                            // Scroll to the button
                            btn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            break;
                        }
                    }
                }
            }
        }

        updateNavigationButtons();
    }

    function updateNavigationButtons() {
        if (!currentPassageMeta || !bibleIndex) {
            chapterNav.hidden = true;
            return;
        }

        chapterNav.hidden = false;

        const { testament, book, chapter } = currentPassageMeta;
        
        // Check if there's a previous chapter
        let hasPrev = false;
        let hasNext = false;

        for (let tIndex = 0; tIndex < bibleIndex.length; tIndex++) {
            const t = bibleIndex[tIndex];
            if (t.name === testament) {
                for (let bIndex = 0; bIndex < t.books.length; bIndex++) {
                    const b = t.books[bIndex];
                    if (b.name === book) {
                        const cIndex = b.chapters.findIndex(c => c.number === chapter);
                        
                        // Can go previous if not first chapter of first book of first testament
                        hasPrev = !(tIndex === 0 && bIndex === 0 && cIndex === 0);
                        
                        // Can go next if not last chapter of last book of last testament
                        hasNext = !(tIndex === bibleIndex.length - 1 && 
                                   bIndex === t.books.length - 1 && 
                                   cIndex === b.chapters.length - 1);
                        
                        break;
                    }
                }
                break;
            }
        }

        prevChapter.disabled = !hasPrev;
        nextChapter.disabled = !hasNext;
    }

    function getBookNameFromPath(path) {
        // Extract book name from path like "Old Testament/18 Job/job1.md"
        const parts = path.split('/');
        if (parts.length >= 2) {
            const folderName = parts[1];
            return folderName.split(' ').slice(1).join(' '); // Remove number prefix
        }
        return '';
    }

    function getTestamentFromPath(path) {
        const parts = path.split('/');
        return parts[0] || '';
    }

    // ========================================
    // Reading History Functions
    // ========================================
    function saveToHistory(meta) {
        if (!meta || !meta.book || !meta.chapter) return;
        
        try {
            let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
            const version = getCurrentVersion();
            
            // Create history entry
            const entry = {
                book: meta.book,
                chapter: meta.chapter,
                testament: meta.testament,
                path: meta.path,
                version: version,
                timestamp: Date.now()
            };
            
            // Remove duplicate if exists (same book+chapter+version)
            history = history.filter(h => 
                !(h.book === entry.book && h.chapter === entry.chapter && h.version === entry.version)
            );
            
            // Add to front
            history.unshift(entry);
            
            // Limit size
            if (history.length > MAX_HISTORY) {
                history = history.slice(0, MAX_HISTORY);
            }
            
            localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        } catch (err) {
            console.warn('Could not save reading history:', err);
        }
    }
    
    function getReadingHistory() {
        try {
            return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        } catch {
            return [];
        }
    }
    
    function checkResumeReading() {
        const history = getReadingHistory();
        if (history.length === 0) return;
        
        const last = history[0];
        const version = getCurrentVersion();
        
        // Only show resume if same version and recent (within 7 days)
        const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
        if (last.version === version && last.timestamp > sevenDaysAgo) {
            showResumePrompt(last);
        }
    }
    
    function showResumePrompt(entry) {
        // Create a subtle resume banner
        const banner = document.createElement('div');
        banner.className = 'resume-banner';
        banner.innerHTML = `
            <span class="resume-text">📖 Continue reading: <strong>${entry.book} ${entry.chapter}</strong></span>
            <button class="resume-btn" type="button">Resume</button>
            <button class="resume-dismiss" type="button" aria-label="Dismiss">×</button>
        `;
        
        // Insert at top of chapter panel
        const chapterPanel = document.querySelector('.chapter-panel');
        if (chapterPanel) {
            chapterPanel.insertBefore(banner, chapterPanel.firstChild);
            
            banner.querySelector('.resume-btn').addEventListener('click', () => {
                loadChapter(entry);
                banner.remove();
            });
            
            banner.querySelector('.resume-dismiss').addEventListener('click', () => {
                banner.remove();
            });
            
            // Auto-dismiss after 10 seconds
            setTimeout(() => {
                if (banner.parentNode) {
                    banner.style.opacity = '0';
                    setTimeout(() => banner.remove(), 300);
                }
            }, 10000);
        }
    }

    // ========================================
    // Keyboard Shortcuts for Bible Reader
    // ========================================
    document.addEventListener('keydown', (e) => {
        // Don't trigger when typing
        if (e.target.matches('input, textarea, select')) return;
        
        // Left/Right arrows: Navigate chapters
        if (e.key === 'ArrowLeft' && !prevChapter.disabled) {
            navigateChapter(-1);
        } else if (e.key === 'ArrowRight' && !nextChapter.disabled) {
            navigateChapter(1);
        }
        
        // N: Toggle night mode
        if (e.key === 'n' && !e.ctrlKey && !e.metaKey) {
            nightModeToggle.click();
        }
        
        // Home: Go to main site
        if (e.key === 'h' && !e.ctrlKey && !e.metaKey) {
            window.location.href = '/';
        }
    });
});
