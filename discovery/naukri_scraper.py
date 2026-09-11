"""
discovery/naukri_scraper.py

Fast, resilient scraper for Naukri.com.
Uses resource aborting (skipping images/css/fonts) and strict timeouts
to prevent anti-bot hangs and slow page loads.
"""
import asyncio
import os
import re
from playwright.async_api import async_playwright
from discovery.rss_poller import JobListing

class NaukriScraper:
    def __init__(self):
        self.bot_profile_dir = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")
        self.search_urls = [
            "https://www.naukri.com/software-engineer-jobs-in-india?experience=0&jobAge=7",
            "https://www.naukri.com/full-stack-developer-jobs-in-india?experience=0&jobAge=7",
            "https://www.naukri.com/backend-developer-jobs-in-india?experience=0&jobAge=7",
        ]
        
    async def fetch_jobs_async(self):
        print("🕵️‍♂️ Scraping Naukri.com (India's #1 job board)")
        jobs = []
        seen_urls = set()
        
        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.bot_profile_dir,
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                
                for search_url in self.search_urls:
                    if len(jobs) >= 40:
                        break
                        
                    page = await context.new_page()
                    
                    # Block heavy assets to make Naukri load 10x faster and prevent hangs
                    await page.route(
                        re.compile(r"(\.png|\.jpg|\.jpeg|\.gif|\.svg|\.woff|\.woff2|\.css|google-analytics|doubleclick|hotjar)"),
                        lambda route: route.abort()
                    )
                    
                    try:
                        # Set strict 15s timeout on goto
                        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                        await page.wait_for_timeout(2000)
                        
                        # Quick scroll
                        await page.evaluate("window.scrollBy(0, 1000)")
                        await page.wait_for_timeout(1000)
                        
                        job_cards = page.locator("a.title, a[class*='jobTitle'], div.cust-job-tuple a[title]")
                        count = await job_cards.count()
                        
                        for i in range(min(count, 20)):
                            try:
                                card = job_cards.nth(i)
                                title = await card.get_attribute("title") or await card.inner_text()
                                href = await card.get_attribute("href") or ""
                                
                                if not href or href in seen_urls:
                                    continue
                                seen_urls.add(href)
                                
                                if not href.startswith("http"):
                                    href = f"https://www.naukri.com{href}"
                                
                                company = "Naukri Startup"
                                try:
                                    parent = card.locator("xpath=ancestor::div[contains(@class, 'tuple') or contains(@class, 'job')]").first
                                    company_el = parent.locator("a.comp-name, a[class*='companyName'], span.comp-name").first
                                    if await company_el.count() > 0:
                                        company = await company_el.inner_text()
                                except Exception:
                                    pass
                                
                                title = title.strip()
                                if title and len(title) > 3:
                                    jobs.append(JobListing(
                                        id=href,
                                        title=title,
                                        company=company.strip(),
                                        link=href,
                                        description="Details on Naukri job page...",
                                        pub_date="Now"
                                    ))
                            except Exception:
                                continue
                                
                    except Exception as e:
                        print(f"   ⚠️ Naukri search error: {e}")
                    finally:
                        await page.close()
                        
                await context.close()
        except Exception as ex:
            print(f"   ⚠️ Naukri context error: {ex}")
                
        print(f"✅ Found {len(jobs)} jobs on Naukri!")
        return jobs

    def fetch_jobs(self):
        return asyncio.run(self.fetch_jobs_async())

if __name__ == "__main__":
    scraper = NaukriScraper()
    jobs = scraper.fetch_jobs()
    for j in jobs:
        print(f"{j.company} - {j.title} - {j.link}")
