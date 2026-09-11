"""
discovery/himalayas_scraper.py

Scraper for Himalayas — a premier remote startup job platform.
Uses their clean public API for reliable, paywall-free startup job listings.
"""
import requests
import re
import html
from typing import List
from discovery.rss_poller import JobListing

class HimalayasScraper:
    def __init__(self, limit: int = 40):
        # Filter for software-development to get high-relevance engineering roles
        self.api_url = f"https://himalayas.app/jobs/api?category=software-development&limit={limit}"
        
    def clean_html(self, raw_html: str) -> str:
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, ' ', raw_html)
        cleantext = html.unescape(cleantext)
        return ' '.join(cleantext.split())[:3000]

    def fetch_jobs(self) -> List[JobListing]:
        print("🕵️‍♂️ Fetching startup jobs from Himalayas (Free API)...")
        jobs = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(self.api_url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                raw_jobs = data.get("jobs", [])
                
                for r in raw_jobs:
                    job_id = str(r.get("guid", r.get("id", "")))
                    title = r.get("title", "")
                    company = r.get("companyName", "Startup")
                    # Himalayas uses 'applicationLink' for external ATS and 'guid' for posting URL
                    link = r.get("applicationLink") or r.get("guid") or ""
                    desc = self.clean_html(r.get("description", r.get("excerpt", "")))
                    pub_date = str(r.get("pubDate", "Now"))
                    
                    if title and link:
                        jobs.append(JobListing(
                            id=job_id or link,
                            title=title.strip(),
                            company=company.strip(),
                            link=link.strip(),
                            description=desc,
                            pub_date=pub_date
                        ))
            else:
                print(f"❌ Himalayas API returned HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Himalayas fetch error: {e}")
            
        print(f"✅ Discovered {len(jobs)} startup jobs on Himalayas!")
        return jobs

    async def fetch_jobs_async(self) -> List[JobListing]:
        return self.fetch_jobs()

if __name__ == "__main__":
    scraper = HimalayasScraper()
    jobs = scraper.fetch_jobs()
    for j in jobs[:5]:
        print(f"{j.company} - {j.title}: {j.link}")
