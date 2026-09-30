import urllib.request
import time

time.sleep(1)
urls = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/visual/',
    'http://127.0.0.1:8000/man-of-the-month/',
    'http://127.0.0.1:8000/sitemap.xml',
    'http://127.0.0.1:8000/robots.txt'
]

for url in urls:
    try:
        code = urllib.request.urlopen(url).getcode()
        print(f"{url}: {code}")
    except Exception as e:
        print(f"{url}: {e}")
