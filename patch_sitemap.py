import re

with open('app.py', 'r') as f:
    content = f.read()

old_sitemap = """    # Main pages
    main_pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/static/bible.html', 'priority': '0.9', 'changefreq': 'weekly'},
        {'loc': '/static/passage.html', 'priority': '0.7', 'changefreq': 'monthly'},
    ]"""

new_sitemap = """    # Main pages
    main_pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/bible', 'priority': '0.9', 'changefreq': 'weekly'},
        {'loc': '/topics', 'priority': '0.9', 'changefreq': 'weekly'},
    ]

    # Add topic pages
    for topic in BIBLE_TOPICS:
        slug = topic.lower().replace(' ', '-')
        main_pages.append({
            'loc': f'/topics/{slug}',
            'priority': '0.8',
            'changefreq': 'monthly'
        })

    # Add recent community questions
    try:
        shares = database.get_recent_shared_conversations(limit=50)
        for share in shares:
            main_pages.append({
                'loc': f'/q/{share["id"]}',
                'priority': '0.7',
                'changefreq': 'yearly'
            })
    except Exception as e:
        print(f"Warning: Could not fetch recent shares for sitemap: {e}")
"""

content = content.replace(old_sitemap, new_sitemap)

with open('app.py', 'w') as f:
    f.write(content)
