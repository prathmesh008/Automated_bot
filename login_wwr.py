import asyncio
import os
from playwright.async_api import async_playwright

async def login_wwr():
    bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = await browser.new_page()
        print("🌐 Opening WeWorkRemotely...")
        await page.goto("https://weworkremotely.com/job-seekers/account/register")
        
        print("⏳ Please click 'Continue as Prathmesh' and log in.")
        print("I will wait 30 seconds for you to do this...")
        
        await page.wait_for_timeout(30000)
        
        print("✅ Saving session cookies and closing browser cleanly...")
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(login_wwr())
