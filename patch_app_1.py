import re

with open('app.py', 'r') as f:
    content = f.read()

new_routes = """
@app.route('/bible')
def bible_index_default():
    \"\"\"Serve the Bible index page for the default version.\"\"\"
    return bible_index(DEFAULT_VERSION)

@app.route('/bible/<version>')
def bible_index(version):
    \"\"\"Serve the Bible index page showing all books and chapters for SEO.\"\"\"
    # Normalize version
    if version not in BIBLE_INDICES:
        # Check if they are trying to access a book directly via legacy route (e.g. /bible/Genesis)
        # This prevents 404s for old links
        if normalize_book_name(version) and not version.lower() in [v.lower() for v in BIBLE_INDICES.keys()]:
            # They meant to go to a chapter, but forgot the chapter number? Unlikely, but redirect to home just in case
            pass
        version = DEFAULT_VERSION

    index = BIBLE_INDICES.get(version, [])

    # Build version list for template
    available_versions = []
    for code in BIBLE_INDICES.keys():
        available_versions.append({
            'code': code,
            'name': VERSION_NAMES.get(code, code.upper()),
            'short': code.upper()
        })
    available_versions.sort(key=lambda v: (v['code'] != 'kjv', v['name']))

    version_name = VERSION_NAMES.get(version, version.upper())
    canonical_url = url_for('bible_index', version=version, _external=True) if version != DEFAULT_VERSION else url_for('bible_index_default', _external=True)

    return render_template(
        'bible_index.html',
        index=index,
        version=version,
        version_name=version_name,
        available_versions=available_versions,
        canonical_url=canonical_url
    )

@app.route('/bible/<book>/<chapter>')
"""

# Find where to insert it (before bible_chapter_legacy)
content = content.replace("@app.route('/bible/<book>/<chapter>')", new_routes)

with open('app.py', 'w') as f:
    f.write(content)
