import re

def linkify_bible_references(html: str, version: str = 'kjv') -> str:
    bible_ref_pattern = re.compile(r'\b((?:[1-3]\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(\d+):(\d+)(?:-(\d+))?')

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

test_string = "<p>As it says in John 3:16 and 1 Corinthians 13:4-7.</p>"
print(linkify_bible_references(test_string))
