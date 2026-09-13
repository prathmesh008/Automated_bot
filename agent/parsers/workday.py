import asyncio
import os
import re
import time
import imaplib
import email
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv
from agent.ai_form_filler import auto_fill_form_with_ai, find_candidate_resume
from core.profile_loader import load_profile

load_dotenv()

def get_workday_otp(email_addr, app_password, timeout_sec=60):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(email_addr, app_password)
    mail.select("inbox")
    
    print("⏳ Waiting for Workday verification code in email...")
    start = time.time()
    while time.time() - start < timeout_sec:
        status, messages = mail.search(None, '(UNSEEN)')
        if status == "OK" and messages[0]:
            for num in reversed(messages[0].split()):
                status, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                sender = msg.get("From", "")
                subject = msg.get("Subject", "")
                
                if "workday" in sender.lower() or "verification" in subject.lower():
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    match = re.search(r'(?i)code(?: is)?[:\s]+([a-zA-Z0-9]{5,8})', body)
                    if not match:
                        match = re.search(r'\b\d{6}\b', body)
                        
                    if match:
                        code = match.group(1) if match.lastindex else match.group(0)
                        print(f"📬 Found Verification Code: {code}")
                        return code
        time.sleep(5)
    print("❌ Did not receive verification code in time.")
    return None


async def apply_to_workday_job(job_url: str, custom_pitch: str, headless: bool = True):
    bot_profile_dir = os.getenv("CHROME_PROFILE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome_profile"))
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = await browser.new_page()
        profile = load_profile()
        email_addr = os.getenv("WORKDAY_EMAIL_ADDRESS")
        app_password = os.getenv("WORKDAY_EMAIL_APP_PASSWORD")
        bot_password = os.getenv("WORKDAY_PASSWORD", "Prath@9968#Work")
        
        try:
            print(f"🌐 Navigating to Workday: {job_url}")
            await page.goto(job_url)
            await page.wait_for_timeout(3000)
            
            # 1. Click initial Apply button
            apply_btn = page.locator("[data-automation-id='applyButton'], [data-automation-id='applyAndGetJobAlertsButton'], button:has-text('Apply')").first
            if await apply_btn.is_visible(timeout=10000):
                await apply_btn.click()
            else:
                raise Exception("Could not find the 'Apply' button! The job posting might be closed or the URL is invalid.")
            
            # If it asks to "Autofill with Resume" vs "Apply Manually"
            autofill_btn = page.locator("[data-automation-id='autofillWithResume'], [data-automation-id='applyManually'], a:has-text('Autofill')").first
            if await autofill_btn.is_visible(timeout=5000):
                await autofill_btn.click()
                await page.wait_for_timeout(2000)
                
                # Check if resume upload is requested right here
                resume_file = find_candidate_resume(profile)
                if resume_file:
                    file_input = page.locator("input[type='file']").first
                    if await file_input.count() > 0:
                        print(f"   📎 Uploading resume to Workday autofill: {resume_file}")
                        await file_input.set_input_files(resume_file)
                        await page.wait_for_timeout(3000)
                        continue_btn = page.locator("button:has-text('Continue'), button:has-text('Next')").first
                        if await continue_btn.is_visible():
                            await continue_btn.click()
                
            # 2. Check if we hit the Login wall
            create_account_btn = page.locator("[data-automation-id='createAccountButton'], a:has-text('Create Account'), button:has-text('Create Account')").first
            if await create_account_btn.is_visible(timeout=8000):
                print("🔑 Creating new Workday account for this tenant...")
                await create_account_btn.click()
                await page.wait_for_timeout(2000)
                
                # Fill registration form
                await page.get_by_label(re.compile(r"Email", re.IGNORECASE)).fill(email_addr)
                await page.get_by_label(re.compile(r"Password", re.IGNORECASE)).first.fill(bot_password)
                await page.get_by_label(re.compile(r"Verify Password", re.IGNORECASE)).fill(bot_password)
                
                # Checkbox for terms
                checkbox = page.locator("input[type='checkbox']").first
                if await checkbox.is_visible():
                    await checkbox.check()
                    
                await page.locator("button").filter(has_text="Create Account").click()
                
                # 3. Handle OTP if prompted
                otp_input = page.locator("input[type='text']").first
                if await page.locator("text=Verification Code").is_visible(timeout=10000):
                    otp = get_workday_otp(email_addr, app_password)
                    if otp:
                        await otp_input.fill(otp)
                        await page.locator("button").filter(has_text="Verify").click()
                    else:
                        raise Exception("Failed to get Workday verification code from email.")
                        
            print("🚀 Inside Workday Application Flow!")
            
            # 4. Loop through Workday pages (My Information -> My Experience -> Application Questions)
            for step in range(5):
                print(f"🧠 Asking AI to process Workday Page {step+1}...")
                await auto_fill_form_with_ai(page, profile, custom_pitch)
                
                next_btn = page.locator("button").filter(has_text=re.compile(r"^Save and Continue$|^Next$", re.IGNORECASE)).first
                if await next_btn.is_visible():
                    await next_btn.click()
                    await page.wait_for_timeout(3000)
                else:
                    break
                    
            # 5. Final Submit check
            submit_btn = page.locator("button").filter(has_text=re.compile(r"^Submit$", re.IGNORECASE)).first
            if await submit_btn.is_visible():
                if submit_applications:
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    print("✅ Successfully submitted Workday application!")
                else:
                    print("⏸ Test Mode: Reached final Review page. Verified complete (submit withheld for testing).")
                    await page.wait_for_timeout(10000)
            else:
                print("ℹ️ Reached end of Workday wizard flow.")
                
        except Exception as e:
            print(f"❌ Workday application failed: {e}")
            raise e
        finally:
            await browser.close()
