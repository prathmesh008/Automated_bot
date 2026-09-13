"""
agent/parsers/instahyre.py
Platform-specific parser for Instahyre.
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def apply_to_instahyre_job(job_url: str, custom_pitch: str, headless: bool = True):
    print(f"🕵️‍♂️ Routing to deterministic Instahyre Parser for {job_url}")
    bot_profile_dir = os.getenv("CHROME_PROFILE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome_profile"))
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = await browser.new_page()
        
        try:
            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            
            # 1. Look for the Apply button
            apply_btn = page.locator("button#btn-apply, button.apply-btn, button:has-text('Apply')").first
            
            if await apply_btn.is_visible():
                await apply_btn.click()
                await page.wait_for_timeout(2000)
            else:
                applied_btn = page.locator("button.applied-btn, button:has-text('Applied')").first
                if await applied_btn.is_visible():
                    print("✅ Already applied to this job on Instahyre directly!")
                    return
                raise Exception("Could not find the 'Apply' button on Instahyre. Ensure you are logged in.")
                
            # 2. Check for cover letter / note modal
            note_box = page.locator("textarea[name='cover_letter'], textarea").first
            if await note_box.count() > 0 and await note_box.is_visible():
                await note_box.fill(custom_pitch)
                
            # 3. Handle submit button with test mode guard
            submit_btn = page.locator("button:has-text('Submit'), button:has-text('Confirm'), .modal button.btn-primary").first
            if await submit_btn.count() > 0 and await submit_btn.is_visible():
                if submit_applications:
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    print("✅ Successfully submitted Instahyre application!")
                else:
                    print("⏸ Test Mode: Instahyre form ready for submission (submit withheld for testing).")
                    await page.wait_for_timeout(5000)
            else:
                print("✅ Done with Instahyre application flow!")
                
        except Exception as e:
            raise e
        finally:
            await browser.close()
