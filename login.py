import asyncio
import os
from playwright.async_api import async_playwright

async def login():
    bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
    print("🔑 Opening bot's Chrome browser for multi-platform login...")
    print("Log in to all platforms. You have 5 minutes. The browser will close automatically.")
    print("")
    print("Tabs opening:")
    print("  1. Wellfound (wellfound.com)")
    print("  2. Y Combinator (workatastartup.com)")  
    print("  4. Naukri (naukri.com)")
    print("  5. Greenhouse (my.greenhouse.io)")
    print("  6. WeWorkRemotely (weworkremotely.com)")
    print("")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=bot_profile_dir,
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page1 = await browser.new_page()
        await page1.goto("https://wellfound.com/login")
        
        page2 = await browser.new_page()
        await page2.goto("https://www.workatastartup.com/")
        
        page3 = await browser.new_page()
        await page3.goto("https://www.instahyre.com/login/")
        
        page4 = await browser.new_page()
        await page4.goto("https://www.naukri.com/nlogin/login")

        page5 = await browser.new_page()
        await page5.goto("https://my.greenhouse.io/dashboard")

        page6 = await browser.new_page()
        await page6.goto("https://weworkremotely.com/")

        # Wait 1 minute
        await page1.wait_for_timeout(60000)
        await browser.close()
        print("✅ Browser closed. All sessions saved!")
 
if __name__ == "__main__":
    asyncio.run(login())
