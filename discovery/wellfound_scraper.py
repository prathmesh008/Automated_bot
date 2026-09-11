import asyncio
import os
import re
from playwright.async_api import async_playwright
from discovery.rss_poller import JobListing

class WellfoundScraper:
    def __init__(self, search_url="https://wellfound.com/role/l/software-engineer/india"):
        self.search_url = search_url
        self.bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
        
    async def fetch_jobs_async(self):
        print(f"🕵️‍♂️ Scraping Wellfound: {self.search_url}")
        jobs = []
        
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.bot_profile_dir,
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            page = await context.new_page()
            
            try:
                await page.goto(self.search_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(4000)
                
                # Scroll down multiple times to trigger lazy loading
                for _ in range(6):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)
                
                # Locate all links to companies and jobs sequentially
                links = await page.locator("a[href*='/company/'], a[href*='/jobs/']").all()
                current_company = "Wellfound Startup"
                
                for link in links:
                    if len(jobs) >= 50:
                        break
                        
                    href = await link.get_attribute("href")
                    if not href:
                        continue
                        
                    text = await link.inner_text()
                    text = text.strip()
                    if not text:
                        continue
                        
                    if "/company/" in href:
                        current_company = text
                        continue
                        
                    # Filter out navigation endpoints like /jobs/home, /jobs/applications, /jobs/messages
                    ignored_routes = ["/jobs/home", "/jobs/applications", "/jobs/messages", "/jobs/saved", "/jobs/preferences"]
                    if any(r in href for r in ignored_routes):
                        continue
                    
                    # Filter for genuine job posting slugs: e.g., /jobs/4470243-devops-engineer
                    if not re.search(r'/jobs/\d+-[a-zA-Z0-9-]+', href):
                        continue
                    
                    full_link = f"https://wellfound.com{href}" if href.startswith("/") else href
                    
                    if full_link not in [j.link for j in jobs]:
                        jobs.append(JobListing(
                            id=href,
                            title=text,
                            company=current_company,
                            link=full_link,
                            description="Fetching description dynamically requires visiting the page...",
                            pub_date="Now"
                        ))
            except Exception as e:
                print(f"❌ Wellfound Scraping Error: {e}")
            finally:
                await context.close()
                
        print(f"✅ Found {len(jobs)} genuine jobs on Wellfound!")
        return jobs

    def fetch_jobs(self):
        """Synchronous wrapper for compatibility with run_daily.py"""
        return asyncio.run(self.fetch_jobs_async())

if __name__ == "__main__":
    scraper = WellfoundScraper()
    jobs = scraper.fetch_jobs()
    for j in jobs:
        print(f"{j.company} - {j.title} - {j.link}")
