import re

with open('app.py', 'r') as f:
    content = f.read()

new_routes = """
@app.route('/bible/<version>/<book>/<chapter>/<verse>')
def bible_verse(version, book, chapter, verse):
    \"\"\"Serve a specific Bible verse with SSR and comparisons.\"\"\"
    try:
        book_name = normalize_book_name(book)
        chapter_num = int(chapter)
        verse_num = int(verse)

        verses = get_verses_for_chapter(version, book_name, chapter_num, BIBLE_DATA_DIR)

        if not verses:
            abort(404)

        verse_text = None
        for v_num_str, v_text in verses:
            if int(v_num_str) == verse_num:
                verse_text = v_text
                break

        if not verse_text:
            abort(404)

        # Get comparisons for other versions
        comparisons = []
        for v_code in BIBLE_INDICES.keys():
            if v_code == version:
                continue
            try:
                comp_verses = get_verses_for_chapter(v_code, book_name, chapter_num, BIBLE_DATA_DIR)
                for comp_v_num, comp_text in comp_verses:
                    if int(comp_v_num) == verse_num:
                        comparisons.append({
                            'version': v_code,
                            'version_name': VERSION_NAMES.get(v_code, v_code.upper()),
                            'text': comp_text
                        })
                        break
            except Exception:
                continue

        proper_book_name = book_name
        version_upper = version.upper()
        version_name = VERSION_NAMES.get(version, version_upper)

        title = f"{proper_book_name} {chapter_num}:{verse_num} - {version_name} | WWAIJD"
        description = f"Read {proper_book_name} {chapter_num}:{verse_num} in the {version_name}. {verse_text[:100]}..."
        canonical_url = url_for('bible_verse', version=version, book=proper_book_name, chapter=chapter_num, verse=verse_num, _external=True)

        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{proper_book_name} {chapter_num}:{verse_num}",
            "description": description,
            "inLanguage": "en",
            "isPartOf": {
                "@type": "Book",
                "name": "The Holy Bible",
                "bookEdition": f"{version_name}"
            }
        }

        available_versions = []
        for code in BIBLE_INDICES.keys():
            available_versions.append({
                'code': code,
                'name': VERSION_NAMES.get(code, code.upper()),
                'short': code.upper()
            })
        available_versions.sort(key=lambda v: (v['code'] != 'kjv', v['name']))

        return render_template(
            'verse.html',
            title=title,
            description=description,
            canonical_url=canonical_url,
            schema_json=json.dumps(schema),
            book=proper_book_name,
            chapter=chapter_num,
            verse=verse_num,
            verse_text=verse_text,
            version=version,
            version_name=version_name,
            available_versions=available_versions,
            comparisons=comparisons
        )
    except Exception as e:
        print(f"Error serving verse: {e}")
        abort(404)

@app.route('/sitemap.xml')
"""

content = content.replace("@app.route('/sitemap.xml')", new_routes)

with open('app.py', 'w') as f:
    f.write(content)
