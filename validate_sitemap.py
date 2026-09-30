import urllib.request
import xml.etree.ElementTree as ET

def check():
    try:
        # Check robots.txt
        resp = urllib.request.urlopen("http://127.0.0.1:8000/robots.txt")
        robots = resp.read().decode('utf-8')
        print("ROBOTS.TXT:")
        print(robots)

        # Check sitemap.xml
        resp = urllib.request.urlopen("http://127.0.0.1:8000/sitemap.xml")
        sitemap_xml = resp.read().decode('utf-8')
        print("SITEMAP.XML:")
        print(sitemap_xml)
        
        # Parse XML
        root = ET.fromstring(sitemap_xml)
        print("XML PARSED SUCCESSFULLY.")
        print("SITEMAP URLS:")
        for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
            print("-", loc)
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    check()
