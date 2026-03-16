import re

with open('app.py', 'r') as f:
    content = f.read()

new_routes = """
# Common Bible topics for SEO
BIBLE_TOPICS = [
    "Love", "Forgiveness", "Faith", "Hope", "Peace", "Patience",
    "Wisdom", "Strength", "Courage", "Grace", "Mercy", "Salvation",
    "Anxiety", "Fear", "Healing", "Joy", "Marriage", "Money",
    "Prayer", "Family", "Friendship", "Trust", "Worry", "Anger"
]

@app.route('/topics')
def topics_index():
    \"\"\"Serve the topics index page for SEO.\"\"\"
    return render_template(
        'topics_index.html',
        topics=sorted(BIBLE_TOPICS)
    )

@app.route('/topics/<slug>')
def topic_page(slug):
    \"\"\"Serve a specific topic page with retrieved passages for SEO.\"\"\"
    topic_name = slug.replace('-', ' ')

    # Retrieve relevant passages
    passages = []
    if rag:
        try:
            passages = rag.retrieve_passages(topic_name, version=DEFAULT_VERSION)
        except Exception as e:
            print(f"Error retrieving passages for topic {topic_name}: {e}")

    canonical_url = url_for('topic_page', slug=slug, _external=True)

    return render_template(
        'topic.html',
        topic_name=topic_name,
        passages=passages,
        version=DEFAULT_VERSION,
        canonical_url=canonical_url
    )

@app.route('/sitemap.xml')
"""

content = content.replace("@app.route('/sitemap.xml')", new_routes)

with open('app.py', 'w') as f:
    f.write(content)
