"""
agent/parsers/wellfound.py

Platform-specific parser for Wellfound (formerly AngelList) native applications.
Assumes the user is already authenticated via the persistent chrome_profile.
"""
import asyncio
import os
from playwright.async_api import async_playwright
from agent.ai_form_filler import auto_fill_form_with_ai, find_candidate_resume
from core.profile_loader import load_profile

async def apply_to_wellfound_job(job_url: str, custom_pitch: str, headless: bool = True):
    print(f"🕵️‍♂️ Routing to deterministic Wellfound Parser for {job_url}")
    bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
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
            await page.wait_for_timeout(3000)
            
            # 1. Look for the "Apply" button on the job posting
            apply_btn = page.locator("button:has-text('Apply'), a:has-text('Apply')").first
            
            if await apply_btn.is_visible():
                await apply_btn.click()
                await page.wait_for_timeout(2000) # Wait for the modal to open
            else:
                raise Exception("Could not find the 'Apply' button on Wellfound.")
                
            # 2. Check if the modal asks for a password (meaning logged out)
            password_field = page.locator("input[type='password']")
            if await password_field.count() > 0:
                raise Exception("Wellfound is asking for a password! Run login.py to re-authenticate.")
                
            # 3. Use AI to dynamically answer custom questions & attach resume
            profile = load_profile()
            await auto_fill_form_with_ai(page, profile, custom_pitch)

            # 4. Fill custom pitch in note box if present
            note_box = page.locator("textarea").first
            if await note_box.count() > 0 and await note_box.is_visible():
                if await note_box.is_enabled():
                    curr_val = await note_box.input_value()
                    if not curr_val.strip() and custom_pitch:
                        await note_box.fill(custom_pitch)
                else:
                    print("   ⚠️ Textarea is disabled (required question or file upload pending). Pitch copied to clipboard!")
                    try:
                        import pyperclip
                        pyperclip.copy(custom_pitch)
                    except Exception:
                        pass
            
            # 5. Handle submission with test-mode guard
            submit_btn = page.locator("button:has-text('Submit'), button:has-text('Send'), button:has-text('Apply')").last
            if await submit_btn.is_visible():
                if submit_applications:
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    print("✅ Successfully submitted Wellfound application!")
                else:
                    print("⏸ Test Mode: Form filled and validated. Ready for submit (submit withheld for testing).")
                    await page.wait_for_timeout(6000)
            else:
                raise Exception("Could not find the Submit button on the Wellfound modal.")
                
        except Exception as e:
            raise e
        finally:
            await browser.close()
