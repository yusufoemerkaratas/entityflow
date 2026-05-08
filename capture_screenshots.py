import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(color_scheme='dark', viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await page.emulate_media(color_scheme="dark")

        print("Capturing Upload Page...")
        await page.goto("http://localhost:5173/upload")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="docs/screenshots/upload_page.png")

        print("Capturing Comparison View...")
        text_area = page.locator('textarea')
        if await text_area.count() > 0:
            await text_area.first.fill("Alice from EntityFlow lives in Berlin and uses alice@example.com.")
        
        submit_btn = page.locator('button[type="submit"]')
        await submit_btn.click()
        
        await page.wait_for_selector('.results-grid', timeout=10000)
        
        # Click "Run all extractors"
        try:
            await page.click('.extractor-run-all', timeout=5000)
            await page.wait_for_timeout(8000) # wait a bit longer for LLM
        except Exception as e:
            print(f"Could not click run all: {e}")
            
        await page.screenshot(path="docs/screenshots/comparison_view.png")

        print("Capturing Entity Review...")
        try:
            await page.hover('.entity-card', timeout=5000)
            await page.wait_for_timeout(1000)
            await page.screenshot(path="docs/screenshots/entity_review.png")
        except Exception as e:
            print(f"Could not capture entity review: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
