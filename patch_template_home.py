import re

with open('templates/index.html', 'r') as f:
    content = f.read()

old_community = """                    <!-- Community Questions -->
                    <div id="communityQuestions" class="community-questions" style="display: none; margin-top: 2rem;">
                        <div class="verse-of-day-label" style="margin-bottom: 0.5rem;">👥 Community Questions</div>
                        <div id="communityQuestionsList" class="question-pills minimal-pills">
                            <!-- Populated by JS -->
                        </div>
                    </div>"""

new_community = """                    <!-- Community Questions -->
                    <div id="communityQuestions" class="community-questions" style="{% if not recent_shares %}display: none;{% endif %} margin-top: 2rem;">
                        <div class="verse-of-day-label" style="margin-bottom: 0.5rem;">👥 Community Questions</div>
                        <div id="communityQuestionsList" class="question-pills minimal-pills">
                            {% for share in recent_shares %}
                            <a href="/q/{{ share.id }}" class="question-pill" title="{{ share.question }}">
                                {{ share.question[:50] + '...' if share.question|length > 50 else share.question }}
                            </a>
                            {% endfor %}
                            <!-- Populated by JS if needed -->
                        </div>
                    </div>"""

content = content.replace(old_community, new_community)

with open('templates/index.html', 'w') as f:
    f.write(content)
