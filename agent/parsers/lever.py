"""
agent/parsers/lever.py

Platform-specific parser for Lever-hosted company career pages (jobs.lever.co/*).
Lever forms are standard single-page applications with no account registration needed.
"""
import asyncio
import os
import re
from playwright.async_api import Page, async_playwright
from core.profile_loader import load_profile
from agent.ai_form_filler import auto_fill_form_with_ai, find_candidate_resume

async def apply_to_lever_job(job_url: str, custom_pitch: str = "", headless: bool = True):
    print(f"🤖 Routing to deterministic Lever Parser for {job_url}...")
    bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"
    profile = load_profile()
    resume_file = find_candidate_resume(profile)
    
    # Ensure URL targets the apply form
    apply_url = job_url.rstrip("/")
    if not apply_url.endswith("/apply"):
        apply_url += "/apply"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = await browser.new_page()
        
        try:
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)
            
            # Check if apply button exists on intermediate page
            apply_btn = page.locator("a:has-text('Apply for this job'), button:has-text('Apply for this job')").first
            if await apply_btn.is_visible():
                await apply_btn.click()
                await page.wait_for_timeout(2000)
            
            # 1. Fill Lever standard inputs
            field_map = {
                'input[name="name"]': profile.full_name,
                'input[name="email"]': profile.email,
                'input[name="phone"]': profile.phone,
                'input[name="org"]': getattr(profile, "current_company", "Student / Fresher"),
                'input[name="urls[LinkedIn]"]': profile.linkedin,
                'input[name="urls[GitHub]"]': profile.github,
                'input[name="urls[Portfolio]"]': profile.portfolio,
            }
            
            for selector, val in field_map.items():
                if val:
                    loc = page.locator(selector).first
                    if await loc.count() > 0:
                        await loc.fill(val)
                        field_name = selector.replace('input[name="', '').replace('"]', '')
                        print(f"   ✅ Lever filled '{field_name}' -> {val}")
                        
            # 2. Attach Candidate Resume
            if resume_file:
                file_input = page.locator("input[type='file']#resume-upload-input, input[type='file']").first
                if await file_input.count() > 0:
                    print(f"   📎 Attaching resume to Lever: {resume_file}")
                    await file_input.set_input_files(resume_file)
                    await page.wait_for_timeout(2000)
                    print("   ✅ Resume attached to Lever.")

            # 3. Handle any custom company questions with AI Form Filler
            await auto_fill_form_with_ai(page, profile, custom_pitch)
            
            # 4. Handle submission
            submit_btn = page.locator("button#btn-submit, button:has-text('Submit Application')").first
            if await submit_btn.is_visible():
                if submit_applications:
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    print("✅ Lever application submitted successfully!")
                else:
                    print("⏸ Test Mode: Lever form completed and verified (submit withheld).")
                    await page.wait_for_timeout(6000)
            else:
                print("ℹ️ Reached end of Lever form flow.")
                
        except Exception as e:
            print(f"❌ Lever application error: {e}")
            raise e
        finally:
            await browser.close()
