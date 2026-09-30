import os
import re

directories = [
    r"c:\Users\Admin\OneDrive\Desktop\spectrum\frontend",
    r"c:\Users\Admin\OneDrive\Desktop\spectrum\backend",
    r"c:\Users\Admin\OneDrive\Desktop\spectrum\docs",
    r"c:\Users\Admin\OneDrive\Desktop\spectrum\PROJECT_DOCUMENTATION.md"
]

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        # Replacements
        new_content = new_content.replace('SmartWaste', 'CleanLoop')
        new_content = new_content.replace('SMARTWASTE', 'CLEANLOOP')
        
        # Avoid replacing smartwaste_project which is a python package
        # but replace smartwaste in alt texts or descriptions
        new_content = new_content.replace('alt="SmartWaste', 'alt="CleanLoop')
        new_content = new_content.replace('alt="smartwaste', 'alt="cleanloop')
        
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        pass

for d in directories:
    if os.path.isfile(d):
        replace_in_file(d)
    else:
        for root, dirs, files in os.walk(d):
            if '.git' in root or '__pycache__' in root or 'venv' in root:
                continue
            for file in files:
                if file.endswith('.html') or file.endswith('.py') or file.endswith('.md'):
                    replace_in_file(os.path.join(root, file))

print("Rebranding complete.")
