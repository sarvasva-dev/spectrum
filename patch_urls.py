import re

with open('backend/waste_management/urls.py', 'r') as f:
    content = f.read()

if "path('ai/'" not in content:
    content = content.replace(
        "    path('visual/', views.api_playground_view, name='api_playground'),",
        "    path('ai/', views.ai_view, name='ai'),\n    path('api/ai/chat/', views.api_ai_chat_view, name='api_ai_chat'),\n    path('visual/', views.api_playground_view, name='api_playground'),"
    )

with open('backend/waste_management/urls.py', 'w') as f:
    f.write(content)
