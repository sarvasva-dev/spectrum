import os

html_dir = r"c:\Users\Admin\OneDrive\Desktop\spectrum\frontend\pages"

new_nav_item = """          <li><a href="{% url 'awareness' %}" class="nav-link {% if request.resolver_match.url_name == 'awareness' %}active{% endif %}">Awareness</a></li>
          <li><a href="{% url 'man_of_the_month' %}" class="nav-link {% if request.resolver_match.url_name == 'man_of_the_month' %}active{% endif %}">Man of the Month</a></li>"""

for root, _, files in os.walk(html_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = content.replace('Smart<span class="highlight">Waste</span>', 'Clean<span class="highlight">Loop</span>')
            new_content = new_content.replace('<li><a href="{% url \'awareness\' %}" class="nav-link {% if request.resolver_match.url_name == \'awareness\' %}active{% endif %}">Awareness</a></li>', new_nav_item)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Updated {f}")
