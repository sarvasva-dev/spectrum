import asyncio
from playwright.async_api import async_playwright

async def main():
    base_url = "http://127.0.0.1:8000"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        print("Logging in...")
        await page.goto(base_url + "/login/")
        await page.fill("input[name='username']", "citizen@smartwaste.org")
        await page.fill("input[name='password']", "demo1234")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("load")
        
        print("Visiting /report/")
        await page.goto(base_url + "/report/", wait_until="load")
        await page.screenshot(path="C:/Users/Admin/OneDrive/Desktop/spectrum/report_auth.png", full_page=True)
        
        map_exists = await page.evaluate("document.querySelector('.folium-map-container') !== null")
        print(f"Map exists on report: {map_exists}")
        
        # Test GET API Visualizer Health Check API visually
        print("Visiting /visual/")
        await page.goto(base_url + "/visual/", wait_until="load")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
