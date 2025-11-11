document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const path = params.get('path');
    const start = params.get('start');
    const end = params.get('end');
    const fallbackBook = params.get('book');
    const fallbackChapter = params.get('chapter');
    const fallbackReference = params.get('reference');

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
        end
    });

    async function fetchPassage({ path: relativePath, book, chapter, start: startVerse, end: endVerse }) {
        const url = new URL('/api/bible-passage', window.location.origin);
        if (relativePath) {
            url.searchParams.set('path', relativePath);
        } else {
            if (book) url.searchParams.set('book', book);
            if (chapter) url.searchParams.set('chapter', chapter);
        }
        if (startVerse) url.searchParams.set('start', startVerse);
        if (endVerse) url.searchParams.set('end', endVerse);

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
