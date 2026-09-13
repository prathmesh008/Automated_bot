"""
agent/browser_agent.py

Generic fallback Playwright agent for platforms that don't have
a dedicated parser (e.g., random company career pages, Naukri, etc.).
Uses fuzzy text matching to find Apply buttons and fill forms.
"""
import asyncio
import os
import re
from playwright.async_api import async_playwright

async def apply_to_job(job_url: str, custom_pitch: str):
    print(f"🤖 Starting generic Playwright Agent for: {job_url}")
    bot_profile_dir = os.getenv("CHROME_PROFILE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chrome_profile"))
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"
    is_headless = os.getenv("HEADLESS_MODE", "false").lower() == "true"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=is_headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = await context.new_page()
        
        try:
            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Look for the "Apply" button
            apply_btn = page.locator("a, button").filter(has_text=re.compile(r"\bApply\b", re.IGNORECASE)).first
            
            if await apply_btn.is_visible():
                print("🖱️ Found Apply button. Clicking it...")
                try:
                    # Catch if it opens in a new tab (like WeWorkRemotely does)
                    async with context.expect_page(timeout=5000) as new_page_info:
                        await apply_btn.click()
                    print("📄 It opened a new tab! Switching context...")
                    page = await new_page_info.value
                    await page.wait_for_load_state("domcontentloaded")
                except Exception:
                    pass
                
                await page.wait_for_timeout(3000)
                
                print("🧠 Handing over the page to the AI Form Filler...")
                from agent.ai_form_filler import auto_fill_form_with_ai
                from core.profile_loader import load_profile
                profile = load_profile()
                
                # Loop through up to 3 pages (e.g., Reg Wall -> App Page 1 -> App Page 2)
                for step in range(3):
                    print(f"📄 Processing Page {step + 1} of Application Flow...")
                    
                    # 1. Prefer Logging In over Signing Up
                    try:
                        signin_link = page.locator("a").filter(has_text=re.compile(r"^Sign in.*|^Log in.*", re.IGNORECASE)).first
                        if await signin_link.is_visible(timeout=1000):
                            print("🖱️ Found 'Sign In' link! Switching to Login mode...")
                            await signin_link.click()
                            await page.wait_for_timeout(3000)
                    except Exception:
                        pass
                        
                    # 2. Hand over to AI Form Filler
                    await auto_fill_form_with_ai(page, profile, custom_pitch)
                    
                    # 3. Try to click Continue/Next/Submit/Sign In
                    next_btn = page.locator("button, input[type='submit']").filter(has_text=re.compile(r"^Continue$|^Next$|^Submit Application$|^Apply$|^Sign in$", re.IGNORECASE)).first
                    if await next_btn.is_visible(timeout=2000):
                        btn_text = await next_btn.get_attribute("value") or await next_btn.inner_text()
                        print(f"🖱️ Clicking '{btn_text}'...")
                        
                        # Guard final submission if text is Submit
                        if "submit" in str(btn_text).lower() and not submit_applications:
                            print("⏸ Test Mode: Submit button located and verified (submission withheld).")
                            await page.wait_for_timeout(5000)
                            return {"status": "staged_for_review", "message": "Form completed in test mode."}
                            
                        await next_btn.click()
                        await page.wait_for_timeout(4000)
                        
                        # Hijack check: onboarding or pricing wall
                        if "onboarding" in page.url.lower() or "pricing" in page.url.lower():
                            print("⚠️ Detected an onboarding/upsell wall! Re-navigating to job...")
                            await page.goto(job_url, wait_until="domcontentloaded")
                            await page.wait_for_timeout(3000)
                            
                            apply_btn2 = page.locator("a, button").filter(has_text=re.compile(r"^Apply|Apply for this position|Apply Now", re.IGNORECASE)).first
                            if await apply_btn2.is_visible():
                                print("🖱️ Clicking Apply again...")
                                try:
                                    async with context.expect_page(timeout=5000) as new_page_info:
                                        await apply_btn2.click()
                                    page = await new_page_info.value
                                    await page.wait_for_load_state("domcontentloaded")
                                except Exception:
                                    pass
                            await page.wait_for_timeout(3000)
                    else:
                        break
                        
                print("✅ Generic agent finished flow!")
                return {"status": "success", "message": "Interacted with the form."}
                    
            else:
                raise Exception("Could not find the 'Apply' button on the page.")
                
        except Exception as e:
            print(f"❌ Generic Agent failed: {e}")
            raise e
        finally:
            await context.close()
