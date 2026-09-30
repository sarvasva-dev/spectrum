import re

def update_urls():
    filepath = r"c:\Users\Admin\OneDrive\Desktop\spectrum\backend\waste_management\urls.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_paths = """
    path('man-of-the-month/', views.man_of_the_month_view, name='man_of_the_month'),
    path('man-of-the-month/<slug:slug>/', views.man_of_the_month_view, name='man_of_the_month_slug'),
"""
    if "man-of-the-month" not in content:
        content = content.replace("    # Public Pages\n", "    # Public Pages\n" + new_paths)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("urls.py updated.")

if __name__ == "__main__":
    update_urls()
