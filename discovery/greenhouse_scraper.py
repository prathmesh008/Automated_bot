import asyncio
import os
from playwright.async_api import async_playwright
from discovery.rss_poller import JobListing

class GreenhouseSearchScraper:
    def __init__(self, search_url: str):
        self.search_url = search_url
        self.bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
        
    async def fetch_jobs_async(self):
        print(f"🕵️‍♂️ Scraping Greenhouse Job Board: {self.search_url}")
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
                await page.wait_for_timeout(5000) # Wait for React SPA to render job cards
                
                # Scroll a bit
                for _ in range(5):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)
                
                # Look for links/elements containing job listings
                # Also look for any data-qa or data-testid attributes on job cards
                # Greenhouse usually links out to boards.greenhouse.io or has /jobs/ in URL
                
                # We'll use a combined approach with locators
                job_links = await page.locator("a[href*='/jobs/'], a[href*='boards.greenhouse.io'], [data-testid*='job'], [data-qa*='job']").all()
                
                for element in job_links:
                    if len(jobs) >= 30:
                        break
                        
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    href = None
                    if tag_name == 'a':
                        href = await element.get_attribute("href")
                    else:
                        # If it's a job card container, try to find an anchor inside
                        anchors = await element.locator("a").all()
                        if anchors:
                            href = await anchors[0].get_attribute("href")
                            element = anchors[0]
                    
                    if not href or ("/jobs/" not in href and "boards.greenhouse.io" not in href):
                        continue
                        
                    title_text = await element.inner_text()
                    title_text = title_text.strip() or "Software Engineer"
                    
                    if href not in [j.link for j in jobs]:
                        jobs.append(JobListing(
                            id=href,
                            title=title_text,
                            company="Greenhouse Startup",
                            link=href,
                            description="Details to be fetched on apply page...",
                            pub_date="Now"
                        ))
            except Exception as e:
                print(f"❌ Greenhouse Board Scraping Error: {e}")
            finally:
                await context.close()
                
        print(f"✅ Found {len(jobs)} jobs on the Greenhouse board!")
        return jobs

    def fetch_jobs(self):
        return asyncio.run(self.fetch_jobs_async())

if __name__ == "__main__":
    # Example usage
    scraper = GreenhouseSearchScraper("https://my.greenhouse.io/jobs")
    jobs = scraper.fetch_jobs()
    for j in jobs:
        print(f"{j.company} - {j.title} - {j.link}")
