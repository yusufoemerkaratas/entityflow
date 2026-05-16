import asyncio
import json
import os
import time
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = os.getenv("SCREENSHOT_BASE_URL", "http://127.0.0.1:5175")
API_BASE_URL = os.getenv("SCREENSHOT_API_BASE_URL", "http://127.0.0.1:8001")
ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
SAMPLE_IMAGE = ROOT / "docs" / "demo-images" / "bizay-business-card-mock.png"


async def wait_for_app(page, path: str) -> None:
    await page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
    await page.wait_for_timeout(1200)


async def navigate_spa(page, path: str) -> None:
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.evaluate(
        """targetPath => {
            window.history.pushState({}, "", targetPath)
            window.dispatchEvent(new PopStateEvent("popstate"))
        }""",
        path,
    )
    await page.wait_for_timeout(1200)


def create_document() -> int:
    payload = {
        "text": (
            "Lukas Weber from TechNova GmbH works in Berlin. "
            f"Contact: admin@technova.example, +49 151 00000001. Ref {time.time_ns()}"
        ),
        "source_type": "manual",
    }
    request = urllib.request.Request(
        f"{API_BASE_URL}/documents",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    return int(data["id"])


async def capture_dashboard(page) -> None:
    print("Capturing dashboard...")
    await wait_for_app(page, "/")
    await page.screenshot(path=str(SCREENSHOT_DIR / "dashboard_home.png"))


async def capture_upload_and_document(page) -> None:
    print("Capturing upload page...")
    await wait_for_app(page, "/upload")
    await page.screenshot(path=str(SCREENSHOT_DIR / "upload_page.png"))

    document_id = create_document()
    await navigate_spa(page, f"/documents/{document_id}")
    await page.wait_for_selector(".results-grid", timeout=15000)
    await page.wait_for_timeout(1000)

    print("Running extractors for review screenshot...")
    await page.locator(".extractor-run-all").click()
    await page.wait_for_timeout(5000)

    print("Capturing document comparison...")
    await page.screenshot(path=str(SCREENSHOT_DIR / "comparison_view.png"))

    await page.locator(".entity-card").first.hover()
    await page.wait_for_timeout(600)
    await page.screenshot(path=str(SCREENSHOT_DIR / "entity_review.png"))


async def capture_vision(page) -> None:
    print("Capturing vision upload...")
    await wait_for_app(page, "/")
    await page.get_by_role("link", name="Vision OCR").click()
    await page.wait_for_timeout(1500)
    await page.wait_for_selector("#vision-file-input", timeout=10000)
    await page.screenshot(path=str(SCREENSHOT_DIR / "vision-upload.png"))

    print("Uploading sample image and running OCR pipeline...")
    await page.locator("#vision-file-input").set_input_files(str(SAMPLE_IMAGE))
    await page.wait_for_timeout(1000)
    await page.locator(".vision-primary-button").nth(1).click()
    await page.wait_for_timeout(5000)
    await page.screenshot(path=str(SCREENSHOT_DIR / "vision-result.png"))


async def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            color_scheme="dark",
            viewport={"width": 1280, "height": 920},
        )
        page = await context.new_page()
        await page.emulate_media(color_scheme="dark")

        await capture_dashboard(page)
        await capture_upload_and_document(page)
        await capture_vision(page)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
