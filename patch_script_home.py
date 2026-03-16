import re

with open('static/script.js', 'r') as f:
    content = f.read()

old_script = """    async function loadCommunityQuestions() {
        const container = document.getElementById('communityQuestions');
        const list = document.getElementById('communityQuestionsList');

        if (!container || !list) return;

        try {
            const response = await fetch('/api/recent-shares?limit=6');
            if (!response.ok) return;

            const data = await response.json();
            const shares = data.shares || [];

            if (shares.length === 0) return;

            list.innerHTML = '';
            shares.forEach(share => {"""

new_script = """    async function loadCommunityQuestions() {
        const container = document.getElementById('communityQuestions');
        const list = document.getElementById('communityQuestionsList');

        // Only fetch if not already populated by SSR
        if (!container || !list || list.children.length > 0) return;

        try {
            const response = await fetch('/api/recent-shares?limit=6');
            if (!response.ok) return;

            const data = await response.json();
            const shares = data.shares || [];

            if (shares.length === 0) return;

            list.innerHTML = '';
            shares.forEach(share => {"""

content = content.replace(old_script, new_script)

with open('static/script.js', 'w') as f:
    f.write(content)
