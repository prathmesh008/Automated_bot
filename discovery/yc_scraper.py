import asyncio
import os
import re
from playwright.async_api import async_playwright
from discovery.rss_poller import JobListing

class YCScraper:
    def __init__(self, search_url="https://www.workatastartup.com/jobs?demographic=any&hasEquity=any&hasSalary=any&industry=any&interviewProcess=any&jobType=any&layout=list-view&remote=any"):
        self.search_url = search_url
        self.bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
        
    async def fetch_jobs_async(self):
        print(f"🕵️‍♂️ Scraping Y Combinator (Work at a Startup): {self.search_url}")
        jobs = []
        
        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.bot_profile_dir,
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                page = await context.new_page()
                
                try:
                    await page.goto(self.search_url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(3000)
                    
                    # Scroll to trigger dynamic loading of jobs
                    for _ in range(5):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                    
                    # Find all links on page
                    job_links = await page.locator("a[href*='/jobs/'], a[href*='/companies/']").all()
                    
                    ignored_patterns = [
                        "/jobs/l/", "/jobs/r/", "/jobs/san-francisco", "/jobs/new-york", 
                        "/jobs/los-angeles", "/jobs/designer", "/jobs/marketing", 
                        "/jobs/sales", "/jobs/product-manager", "/jobs/operations", 
                        "/jobs/support", "/jobs/applied", "/jobs/messages"
                    ]
                    
                    for link in job_links:
                        if len(jobs) >= 50:
                            break
                            
                        href = await link.get_attribute("href")
                        if not href:
                            continue
                        
                        # Discard category landing page links
                        if any(ign in href for ign in ignored_patterns):
                            continue
                            
                        # Must match job posting ID or job slug
                        if not re.search(r'/jobs/\d+', href) and not re.search(r'/companies/[^/]+/jobs/\d+', href) and not re.search(r'/jobs/[a-zA-Z0-9-]+-\d+', href):
                            continue
                            
                        full_link = f"https://www.workatastartup.com{href}" if href.startswith("/") else href
                        
                        title_text = await link.inner_text()
                        title_text = title_text.strip()
                        if not title_text or any(ign in title_text.lower() for ign in ["view all", "privacy", "terms", "jobs in", "all jobs"]):
                            continue
                            
                        company_name = "Y Combinator Startup"
                        if " at " in title_text:
                            parts = title_text.split(" at ")
                            if len(parts) > 1:
                                company_name = parts[-1].strip()
                                title_text = parts[0].strip()
                        
                        if full_link not in [j.link for j in jobs]:
                            jobs.append(JobListing(
                                id=href,
                                title=title_text,
                                company=company_name,
                                link=full_link,
                                description="Details to be fetched on apply page...",
                                pub_date="Now"
                            ))
                except Exception as e:
                    print(f"❌ YC Scraping Error: {e}")
                finally:
                    await context.close()
        except Exception as ex:
            print(f"❌ YC Context Error: {ex}")
                
        print(f"✅ Found {len(jobs)} genuine job postings on YC!")
        return jobs

    def fetch_jobs(self):
        return asyncio.run(self.fetch_jobs_async())

if __name__ == "__main__":
    scraper = YCScraper()
    jobs = scraper.fetch_jobs()
    for j in jobs:
        print(f"{j.company} - {j.title} - {j.link}")
