import sys
import os

_venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    try:
        import playwright
    except ImportError:
        os.execv(_venv_python, [_venv_python] + sys.argv)

import asyncio
from playwright.async_api import async_playwright
from core.profile_loader import load_profile
from core.qa_matcher import QAMatcher
from agent.parsers.greenhouse import fill_greenhouse_application


async def apply_to_greenhouse_job(job_url: str, headless: bool = True):
    profile = load_profile()

    if profile.load_warnings:
        print(f"⚠ Applying with {len(profile.load_warnings)} blanked TODO field(s): {profile.load_warnings}")

    matcher = QAMatcher(bank_path="profile/screening_qa_bank.yaml")
    bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = await browser.new_page()
        await page.goto(job_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        result = await fill_greenhouse_application(page, profile, matcher)

        if result["needs_review"]:
            print(f"⏸ Holding for manual review: {result['needs_review']}")
            raise Exception(f"Greenhouse form has {len(result['needs_review'])} question(s) needing manual review")
        else:
            submit_btn = page.locator("button[type='submit'], input[type='submit']").first
            if await submit_btn.count() > 0:
                if submit_applications:
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    print(f"✅ Auto-submitted Greenhouse application with {result['auto_filled']} custom field(s).")
                else:
                    print(f"⏸ Test Mode: Auto-filled {result['auto_filled']} custom field(s). Ready for submit (submit withheld for testing).")
                    await page.wait_for_timeout(5000)
            else:
                print(f"✅ Auto-filled {result['auto_filled']} custom field(s) but could not find submit button.")

        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_url = sys.argv[1]
    else:
        print("Usage: python test_greenhouse.py <greenhouse_job_url>")
        sys.exit(1)
        
    asyncio.run(apply_to_greenhouse_job(job_url, headless=False))
