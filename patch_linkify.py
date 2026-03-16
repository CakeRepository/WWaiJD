import re

with open('app.py', 'r') as f:
    content = f.read()

linkify_func = """
def linkify_bible_references(html: str, version: str = DEFAULT_VERSION) -> str:
    \"\"\"
    Converts Bible references in text to anchor tags for SEO and navigation.
    Matches formats like "Proverbs 4:27" or "Matthew 5:3-10".
    \"\"\"
    # Pattern to match Bible references like "Proverbs 4:27" or "Matthew 5:3-10"
    # Matches: Book name (1-3 words) + Chapter:Verse or Chapter:Verse-Verse
    bible_ref_pattern = re.compile(r'\\b((?:[1-3]\\s*)?[A-Z][a-z]+(?:\\s+[A-Z][a-z]+){0,2})\\s+(\\d+):(\\d+)(?:-(\\d+))?')

    def replacer(match):
        book = match.group(1).strip()
        chapter = match.group(2)
        verse_start = match.group(3)
        verse_end = match.group(4)

        reference = f"{book} {chapter}:{verse_start}"
        if verse_end:
            reference += f"-{verse_end}"

        safe_book = book.replace(' ', '%20')
        url = f"/bible/{version}/{safe_book}/{chapter}#{verse_start}"

        return f'<a href="{url}" class="bible-ref-link" data-book="{book}" data-chapter="{chapter}" data-verse-start="{verse_start}" data-verse-end="{verse_end or verse_start}" title="{reference}">{reference}</a>'

    return bible_ref_pattern.sub(replacer, html)

@app.route('/q/<share_id>')
"""

content = content.replace("@app.route('/q/<share_id>')", linkify_func)

# Now update shared_page to use it
old_render = "answer_html = markdown.markdown(data['answer'])"
new_render = """answer_html = markdown.markdown(data['answer'])
        answer_html = linkify_bible_references(answer_html, data.get('version', DEFAULT_VERSION))"""

content = content.replace(old_render, new_render)

with open('app.py', 'w') as f:
    f.write(content)
