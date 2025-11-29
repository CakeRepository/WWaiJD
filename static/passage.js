document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const path = params.get('path');
    const start = params.get('start');
    const end = params.get('end');
    const fallbackBook = params.get('book');
    const fallbackChapter = params.get('chapter');
    const fallbackReference = params.get('reference');
    const version = params.get('version') || 'kjv';

    // Version Dropdown Elements
    const versionDropdown = document.getElementById('versionDropdown');
    const versionBtn = document.getElementById('versionBtn');
    const versionMenu = document.getElementById('versionMenu');
    const currentVersionDisplay = document.getElementById('currentVersionDisplay');

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

    // Load Versions
    loadVersions();

    async function loadVersions() {
        if (!versionMenu) return;
        try {
            const response = await fetch('/api/versions');
            const data = await response.json();
            if (data.versions && data.versions.length > 0) {
                versionMenu.innerHTML = '';
                
                let foundCurrent = false;

                data.versions.forEach(v => {
                    const option = document.createElement('div');
                    option.className = 'version-option';
                    if (v.code === version) {
                        option.classList.add('active');
                        if (currentVersionDisplay) currentVersionDisplay.textContent = v.short;
                        foundCurrent = true;
                    }
                    
                    option.innerHTML = `
                        <span class="version-code">${v.short}</span>
                        <span class="version-name">${v.name}</span>
                    `;
                    
                    option.addEventListener('click', () => {
                        // Reload with new version
                        const newUrl = new URL(window.location);
                        newUrl.searchParams.set('version', v.code);
                        window.location.href = newUrl.toString();
                    });
                    
                    versionMenu.appendChild(option);
                });
                
                if (!foundCurrent && data.versions.length > 0) {
                    // If current version not found in list, just show it as is or default
                    if (currentVersionDisplay) currentVersionDisplay.textContent = version.toUpperCase();
                }
            }
        } catch (err) {
            console.warn('Could not load versions:', err);
        }
    }

    const titleEl = document.getElementById('passageTitle');
    const subtitleEl = document.getElementById('passageSubtitle');
    const bodyEl = document.getElementById('passageBody');
    const errorEl = document.getElementById('passageError');
    const loadingEl = document.getElementById('passageLoading');
    const nightModeToggle = document.getElementById('nightModeToggle');

    // Initialize night mode
    let isNightMode = localStorage.getItem('nightMode') === 'true';
    if (isNightMode) {
        document.body.classList.add('night-mode');
        nightModeToggle.textContent = '🌙';
    }

    // Night mode toggle
    nightModeToggle.addEventListener('click', () => {
        isNightMode = !isNightMode;
        document.body.classList.toggle('night-mode');
        nightModeToggle.textContent = isNightMode ? '🌙' : '☀️';
        localStorage.setItem('nightMode', isNightMode);
    });

    const hasPath = Boolean(path);
    const hasReference = Boolean(fallbackBook && fallbackChapter);

    if (!hasPath && !hasReference) {
        loadingEl.hidden = true;
        showError('Missing passage path or reference.', errorEl);
        return;
    }

    if (fallbackBook && fallbackChapter) {
        titleEl.textContent = `✟ ${fallbackBook} ${fallbackChapter}`;
    }
    if (fallbackReference) {
        subtitleEl.textContent = fallbackReference;
    }

    fetchPassage({
        path,
        book: fallbackBook,
        chapter: fallbackChapter,
        start,
        end,
        version
    });

    async function fetchPassage({ path: relativePath, book, chapter, start: startVerse, end: endVerse, version }) {
        const url = new URL('/api/bible-passage', window.location.origin);
        if (relativePath) {
            url.searchParams.set('path', relativePath);
        } else {
            if (book) url.searchParams.set('book', book);
            if (chapter) url.searchParams.set('chapter', chapter);
        }
        if (startVerse) url.searchParams.set('start', startVerse);
        if (endVerse) url.searchParams.set('end', endVerse);
        if (version) url.searchParams.set('version', version);

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unable to load passage.');
            }

            renderPassage(data);
        } catch (err) {
            showError(err.message, errorEl);
        } finally {
            loadingEl.hidden = true;
        }
    }

    function renderPassage(data) {
        const highlight = data.highlight || {};
        const highlightStart = parseInt(highlight.start, 10);
        const highlightEnd = parseInt(highlight.end, 10) || highlightStart;

        titleEl.textContent = `${data.book} ${data.chapter}`;
        subtitleEl.textContent = buildSubtitle(data, highlightStart, highlightEnd);

        // Update dynamic SEO meta tags
        updateMetaTags(data, highlightStart, highlightEnd);

        bodyEl.innerHTML = '';
        if (!data.verses || data.verses.length === 0) {
            bodyEl.innerHTML = '<p>We could not parse this chapter.</p>';
        } else {
            data.verses.forEach((verse) => {
                const verseRow = document.createElement('div');
                verseRow.className = 'verse-row';

                const verseNumber = document.createElement('div');
                verseNumber.className = 'verse-number';
                verseNumber.textContent = verse.number;

                const verseText = document.createElement('div');
                verseText.className = 'verse-text';
                verseText.textContent = verse.text;

                verseRow.appendChild(verseNumber);
                verseRow.appendChild(verseText);

                if (isHighlighted(verse.number, highlightStart, highlightEnd)) {
                    verseRow.classList.add('highlight');
                }

                bodyEl.appendChild(verseRow);
            });
        }

        bodyEl.hidden = false;
    }

    function updateMetaTags(data, start, end) {
        const book = data.book;
        const chapter = data.chapter;
        const testament = data.testament || '';
        
        // Build verse range text
        let verseRange = '';
        if (start && end && start !== end) {
            verseRange = `:${start}-${end}`;
        } else if (start) {
            verseRange = `:${start}`;
        }
        
        // Get first verse text for description
        let firstVerseText = '';
        if (data.verses && data.verses.length > 0) {
            firstVerseText = data.verses[0].text.substring(0, 150) + '...';
        }
        
        // Update title
        const pageTitle = `${book} ${chapter}${verseRange} - ${versionName} | WWAIJD`;
        document.title = pageTitle;
        document.getElementById('dynamicTitle').textContent = pageTitle;
        
        // Update description
        const description = firstVerseText 
            ? `Read ${book} Chapter ${chapter}${verseRange} from the ${versionName}. "${firstVerseText}" Free online Bible study.`
            : `Read ${book} Chapter ${chapter} from the ${versionName}. ${testament}. Free online Bible study.`;
        document.getElementById('dynamicDescription').setAttribute('content', description);
        
        // Update canonical URL
        const canonicalUrl = `https://wwaijd.org/static/passage.html?book=${encodeURIComponent(book)}&chapter=${chapter}&version=${version}`;
        document.getElementById('dynamicCanonical').setAttribute('href', canonicalUrl);
        
        // Update Open Graph tags
        document.getElementById('dynamicOgUrl').setAttribute('content', canonicalUrl);
        document.getElementById('dynamicOgTitle').setAttribute('content', `${book} ${chapter}${verseRange} - ${versionName}`);
        document.getElementById('dynamicOgDescription').setAttribute('content', description);
        
        // Update Twitter tags
        document.getElementById('dynamicTwitterUrl').setAttribute('content', canonicalUrl);
        document.getElementById('dynamicTwitterTitle').setAttribute('content', `${book} ${chapter}${verseRange} - ${versionShort}`);
        document.getElementById('dynamicTwitterDescription').setAttribute('content', description);
        
        // Update structured data
        const schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": `${book} ${chapter}${verseRange}`,
            "description": description,
            "inLanguage": "en",
            "isPartOf": {
                "@type": "Book",
                "name": "The Holy Bible",
                "bookEdition": versionName
            },
            "about": {
                "@type": "Thing",
                "name": book,
                "description": `${book} from the ${testament}`
            }
        };
        
        document.getElementById('passageSchema').textContent = JSON.stringify(schema, null, 2);
    }
});

function showError(message, errorEl) {
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function isHighlighted(verseNumber, start, end) {
    const num = parseInt(verseNumber, 10);
    if (Number.isNaN(num) || !start) {
        return false;
    }
    const endValue = end || start;
    return num >= start && num <= endValue;
}

function buildSubtitle(data, start, end) {
    const parts = [];
    if (data.testament) {
        parts.push(data.testament);
    }
    if (start) {
        const focus = end && end !== start ? `${start}–${end}` : start;
        parts.push(`Focus: verses ${focus}`);
    }
    return parts.join(' • ');
}
