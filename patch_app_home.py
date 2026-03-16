import re

with open('app.py', 'r') as f:
    content = f.read()

# Modify index() to fetch recent shares
old_index = """@app.route('/')
def index():
    \"\"\"
    Serve the main page (index.html).

    Returns:
        Response: The index.html file content.
    \"\"\"
    try:
        database.increment_visit_count()
    except Exception as e:
        print(f"Error incrementing visit count: {e}")
    return render_template('index.html')"""

new_index = """@app.route('/')
def index():
    \"\"\"
    Serve the main page (index.html).

    Returns:
        Response: The index.html file content.
    \"\"\"
    try:
        database.increment_visit_count()
    except Exception as e:
        print(f"Error incrementing visit count: {e}")

    # Fetch recent shared questions for SEO and initial render
    recent_shares = []
    try:
        recent_shares = database.get_recent_shared_conversations(limit=6)
    except Exception as e:
        print(f"Error fetching recent shares: {e}")

    return render_template('index.html', recent_shares=recent_shares)"""

content = content.replace(old_index, new_index)

with open('app.py', 'w') as f:
    f.write(content)
