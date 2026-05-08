import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(color_scheme='dark', viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await page.emulate_media(color_scheme="dark") # Force it on the page level too!
        await page.goto("http://localhost:5173/upload")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="test_dark.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
