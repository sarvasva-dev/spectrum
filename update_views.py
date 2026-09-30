import re

def update_views():
    filepath = r"c:\Users\Admin\OneDrive\Desktop\spectrum\backend\waste_management\views.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Append man_of_the_month_view
    motm_code = """

def man_of_the_month_view(request, slug=None):
    \"\"\"
    Public SEO-friendly Man of the Month recognition page.
    Recognizes the citizen with the highest valid complaints in the current month.
    \"\"\"
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Exclude dummy/test data
    valid_complaints = Complaint.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).exclude(
        location__icontains='test'
    ).exclude(
        description__icontains='test'
    )

    complaint_counts = {}
    earliest_submission = {}
    for comp in valid_complaints:
        uid = comp.user_id
        if uid not in complaint_counts:
            complaint_counts[uid] = 0
            earliest_submission[uid] = comp.created_at
        complaint_counts[uid] += 1
        if comp.created_at < earliest_submission[uid]:
            earliest_submission[uid] = comp.created_at

    best_user_id = None
    best_count = -1
    best_time = None

    # Tie handling: highest count, then earliest submission
    for uid, count in complaint_counts.items():
        if count > best_count:
            best_count = count
            best_user_id = uid
            best_time = earliest_submission[uid]
        elif count == best_count:
            if earliest_submission[uid] < best_time:
                best_user_id = uid
                best_time = earliest_submission[uid]

    recognized_citizen = None

    if best_user_id:
        user = User.objects.get(id=best_user_id)
        display_name = user.get_full_name() or user.username
        
        # Area grouping: most frequent location for this user this month
        user_complaints = valid_complaints.filter(user_id=best_user_id)
        from collections import Counter
        areas = [c.location for c in user_complaints if c.location.strip()]
        area = Counter(areas).most_common(1)[0][0] if areas else "Citywide"
            
        import urllib.parse
        safe_slug = urllib.parse.quote(display_name.lower().replace(' ', '-'))

        recognized_citizen = {
            'display_name': display_name,
            'slug': safe_slug,
            'count': best_count,
            'area': area,
        }

    context = {
        'month_name': now.strftime('%B %Y'),
        'citizen': recognized_citizen
    }
    
    return render(request, 'man_of_the_month.html', context)
"""

    if "def man_of_the_month_view" not in content:
        content += motm_code

    # Update sitemap
    new_sitemap = """
def sitemap_xml_view(request):
    \"\"\"
    Search engine sitemap for CleanLoop:
    Provides XML format URLs for all public-facing indexable pages.
    \"\"\"
    domain = "https://cleanloop.sarthakml.in"
    pages = [
        {'loc': f"{domain}/", 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': f"{domain}/awareness/", 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': f"{domain}/visual/", 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f"{domain}/man-of-the-month/", 'changefreq': 'daily', 'priority': '0.9'},
    ]
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for p in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{p["loc"]}</loc>')
        xml.append(f'    <changefreq>{p["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{p["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return HttpResponse("\\n".join(xml), content_type="application/xml")
"""
    # Use regex to replace sitemap_xml_view
    content = re.sub(r'def sitemap_xml_view\(request\):.*?(?=\n\n(?:def |#|$))', new_sitemap.strip(), content, flags=re.DOTALL)

    # Update robots.txt
    new_robots = """
def robots_txt_view(request):
    \"\"\"
    Robots.txt for CleanLoop.
    \"\"\"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /awareness/",
        "Allow: /visual/",
        "Allow: /man-of-the-month/",
        "Disallow: /dashboard/",
        "Disallow: /tracking/",
        "Disallow: /pickup/",
        "Disallow: /admin-portal/",
        "Disallow: /admin/",
        "",
        "Sitemap: https://cleanloop.sarthakml.in/sitemap.xml"
    ]
    return HttpResponse("\\n".join(lines), content_type="text/plain")
"""
    content = re.sub(r'def robots_txt_view\(request\):.*?(?=\n\n(?:def |#|$))', new_robots.strip(), content, flags=re.DOTALL)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("views.py updated successfully.")

if __name__ == "__main__":
    update_views()
