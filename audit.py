import asyncio
import json
from playwright.async_api import async_playwright

urls = [
    ('/', 'landing.png'),
    ('/login/', 'login.png'),
    ('/register/', 'register.png'),
    ('/dashboard/', 'dashboard.png'),
    ('/report/', 'report.png'),
    ('/tracking/', 'tracking.png'),
    ('/pickup/', 'pickup.png'),
    ('/pickup/list/', 'pickup_list.png'),
    ('/awareness/', 'awareness.png'),
    ('/admin-portal/', 'admin.png'),
    ('/visual/', 'visual.png'),
]

async def main():
    base_url = "http://127.0.0.1:8000"
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))
        
        for path, screenshot_name in urls:
            try:
                print(f"Visiting {path}...")
                await page.goto(base_url + path, wait_until="networkidle")
                await page.screenshot(path=f"C:/Users/Admin/OneDrive/Desktop/spectrum/{screenshot_name}", full_page=True)
                results[path] = "SUCCESS"
            except Exception as e:
                results[path] = f"ERROR: {str(e)}"
                
        # Also let's register and login to get a complaint id for the detail pages
        print("Done auditing urls.")
        
        await browser.close()
        
        with open("C:/Users/Admin/OneDrive/Desktop/spectrum/audit_results.json", "w") as f:
            json.dump({"results": results, "console_errors": console_errors}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
