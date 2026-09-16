"""
agent/parsers/yc.py
Platform-specific parser for Y Combinator (Work at a Startup).
"""
import asyncio
import os
import re
from playwright.async_api import async_playwright

from core.profile_loader import load_authenticated_cookies

async def apply_to_yc_job(job_url: str, custom_pitch: str, headless: bool = True):
    # Guard against category landing page URLs
    if not re.search(r'/jobs/\d+', job_url) and not re.search(r'/companies/[^/]+/jobs/\d+', job_url):
        raise ValueError(f"Invalid YC job URL (appears to be a category or landing page): {job_url}")

    print(f"🕵️‍♂️ Routing to deterministic YC Parser for {job_url}")
    bot_profile_dir = os.getenv("CHROME_PROFILE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome_profile"))
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        await load_authenticated_cookies(browser)
        page = await browser.new_page()
        
        try:
            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # 1. Look for the "Apply" button
            apply_btn = page.locator(":is(button, a):has-text('Apply')").first
            
            if await apply_btn.is_visible():
                await apply_btn.click()
                await page.wait_for_timeout(2000) # Wait for the modal
            else:
                raise Exception("Could not find the 'Apply' button on YC. Either logged out or job is closed.")
                
            # 2. Check for login wall
            login_wall = page.locator("input[name='password'], input[name='email']")
            if await login_wall.count() > 0 and await login_wall.first.is_visible():
                raise Exception("YC is asking for a password! Run login.py to re-authenticate.")
                
            # 3. Inject the custom pitch into the text area
            textarea = page.locator("textarea").first
            if await textarea.count() > 0 and await textarea.is_visible():
                pitch_to_send = custom_pitch
                if not pitch_to_send or len(pitch_to_send.strip()) < 50:
                    pitch_to_send = (
                        f"{custom_pitch.strip() if custom_pitch else ''}\n"
                        f"I am a passionate Software Engineer experienced in building scalable web applications, "
                        f"distributed systems, and AI workflows. Excited to discuss how I can contribute to your team!"
                    ).strip()
                await textarea.fill(pitch_to_send)
                await page.wait_for_timeout(1000)
            else:
                print("   No pitch textarea found on YC modal.")
                
            # 4. Controlled submit
            submit_btn = page.locator("button:has-text('Send'), button:has-text('Send application'), button:has-text('Submit')").first
            if await submit_btn.is_visible():
                if submit_applications:
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    print("✅ Successfully submitted YC application!")
                else:
                    print("⏸ Test Mode: Pitch injected and verified. Ready for submit (submit withheld for testing).")
                    await page.wait_for_timeout(3000)
            else:
                raise Exception("Could not find the Submit button on YC.")
                
        except Exception as e:
            raise e
        finally:
            await browser.close()
