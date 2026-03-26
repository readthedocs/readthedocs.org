#!/usr/bin/env python3
"""
Take screenshots for Read the Docs documentation.
Opens a headed browser for you to log in, then captures screenshots automatically.

Usage:
    uv run python take_screenshots.py
"""

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = "https://app.readthedocs.org"
AUTH_FILE = Path(__file__).parent / "playwright_auth.json"
REPO_ROOT = Path(__file__).parent

VIEWPORT = {"width": 1280, "height": 800}

# Screenshots to take: (url_path, output_file)
SCREENSHOTS = [
    # Subprojects
    (
        "/dashboard/djtest/subprojects/",
        "docs/user/img/screenshots/community-project-subproject-list.png",
    ),
    (
        "/dashboard/djtest/subprojects/",
        "docs/user/img/screenshot_subprojects_list.png",
    ),
    (
        "/dashboard/djtest/subprojects/create/",
        "docs/user/img/screenshots/community-project-subproject-create.png",
    ),
    # Webhooks
    (
        "/dashboard/djtest/webhooks/create/",
        "docs/user/img/screenshots/community-project-webhook-create.png",
    ),
    (
        "/dashboard/djtest/webhooks/1485/edit/",
        "docs/user/img/screenshots/community-project-webhook-activity.png",
    ),
    (
        "/dashboard/djtest/webhooks/1485/edit/",
        "docs/user/img/screenshots/community-project-webhook-secret.png",
    ),
    # Import / manual project setup
    (
        "/dashboard/import/",
        "docs/user/img/screenshots/business-project-manual-team-select.png",
    ),
    (
        "/dashboard/import/manual/",
        "docs/user/img/screenshots/business-project-manual-form.png",
    ),
]


async def save_auth(page, path: Path):
    state = await page.context.storage_state()
    path.write_text(json.dumps(state))
    print(f"Auth state saved to {path}")


async def take_screenshots(context):
    page = await context.new_page()
    await page.set_viewport_size(VIEWPORT)

    for url_path, output_rel in SCREENSHOTS:
        url = BASE_URL + url_path
        output = REPO_ROOT / output_rel

        print(f"  {url_path} -> {output_rel}")
        await page.goto(url, wait_until="networkidle")

        # Check redirect to login
        if "/accounts/login/" in page.url:
            print(f"    WARNING: Got redirected to login for {url_path}, skipping")
            continue

        # For webhook-secret, scroll down to show the Secret section
        if "webhook-secret" in output_rel:
            # Scroll the Secret section into view
            await page.evaluate("""
                const h = Array.from(document.querySelectorAll('h3,h4,label,legend'))
                    .find(el => el.textContent.toLowerCase().includes('secret'));
                if (h) h.scrollIntoView({block: 'center'});
            """)
            await page.wait_for_timeout(300)

        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        await page.screenshot(path=str(output), full_page=False)
        print(f"    Saved ({VIEWPORT['width']}x{VIEWPORT['height']})")

    await page.close()


async def main():
    async with async_playwright() as p:
        # Try using saved auth state
        if AUTH_FILE.exists():
            print("Using saved auth state...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(AUTH_FILE), viewport=VIEWPORT)
            # Quick check if still logged in
            page = await context.new_page()
            await page.goto(BASE_URL + "/dashboard/", wait_until="networkidle")
            if "/accounts/login/" in page.url:
                print("Saved auth expired, need to log in again.")
                await page.close()
                await context.close()
                await browser.close()
                AUTH_FILE.unlink()
            else:
                print("Logged in successfully via saved auth.")
                await page.close()
                await take_screenshots(context)
                await context.close()
                await browser.close()
                return

        # Need to log in — open headed browser
        print("\nOpening browser for login...")
        print("Please log in to app.readthedocs.org in the browser window that opens.")
        print("The script will continue automatically once you're logged in.\n")

        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(viewport=VIEWPORT)
        page = await context.new_page()

        await page.goto(
            BASE_URL + "/accounts/login/?next=/dashboard/", wait_until="domcontentloaded"
        )

        # Wait until user is redirected away from the login page
        print("Waiting for login to complete...")
        print("Browser window is open. Waiting up to 5 minutes for login...")
        try:
            await page.wait_for_url(
                lambda url: "/accounts/login/" not in url and "/accounts/" not in url,
                timeout=300_000,
            )
        except Exception:
            print("Timeout waiting for login. Check the browser window.")
            await browser.close()
            return

        print(f"Logged in! Now at: {page.url}")
        await page.close()

        # Save auth state for reuse
        state = await context.storage_state()
        AUTH_FILE.write_text(json.dumps(state))
        print(f"Auth saved to {AUTH_FILE}")

        await take_screenshots(context)

        await context.close()
        await browser.close()

    print("\nDone! All screenshots taken.")


if __name__ == "__main__":
    asyncio.run(main())
