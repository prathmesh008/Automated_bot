"""
discovery/remotive_scraper.py

Scraper for Remotive — official free API, zero paywalls, pure startup listings.
Uses their official public REST API for high reliability and instant fetching.
Strictly filters for software engineering / developer roles.
"""
import requests
import re
import html
from typing import List
from discovery.rss_poller import JobListing

NON_TECH_KEYWORDS = [
    "sales", "sdr", "bdr", "account executive", "marketing", "recruiter", 
    "talent", "hr", "customer support", "customer success", "content", "copywriter",
    "accountant", "legal", "nurse", "medical", "telecaller", "business development"
]

TECH_ROLE_KEYWORDS = [
    "software", "developer", "engineer", "programmer", "backend", "full stack",
    "fullstack", "frontend", "web", "ai", "ml", "devops", "cloud", "sre",
    "data engineer", "platform", "node", "python", "react", "c++", "golang"
]

class RemotiveScraper:
    def __init__(self, category: str = "software-dev", limit: int = 40):
        self.api_url = f"https://remotive.com/api/remote-jobs?category={category}&limit={limit}"
        
    def clean_html(self, raw_html: str) -> str:
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, ' ', raw_html)
        cleantext = html.unescape(cleantext)
        return ' '.join(cleantext.split())[:3000]

    def is_valid_software_role(self, title: str) -> bool:
        t_lower = title.lower()
        if any(re.search(rf"\b{re.escape(bad)}\b", t_lower) for bad in NON_TECH_KEYWORDS):
            return False
        return any(re.search(rf"\b{re.escape(good)}\b", t_lower) for good in TECH_ROLE_KEYWORDS)

    def fetch_jobs(self) -> List[JobListing]:
        print("🕵️‍♂️ Fetching startup jobs from Remotive (Official Free API)...")
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
                    job_id = str(r.get("id", ""))
                    title = r.get("title", "")
                    company = r.get("company_name", "Startup")
                    link = r.get("url", "")
                    desc = self.clean_html(r.get("description", ""))
                    pub_date = r.get("publication_date", "Now")
                    loc = r.get("candidate_required_location", "")
                    
                    loc_lower = loc.lower()
                    if any(c in loc_lower for c in ["us only", "usa only", "uk only", "europe only", "germany only"]):
                        continue
                        
                    # Filter out non-software roles (e.g. sales, marketing)
                    if not self.is_valid_software_role(title):
                        continue
                        
                    if title and link:
                        jobs.append(JobListing(
                            id=job_id or link,
                            title=title.strip(),
                            company=company.strip(),
                            link=link.strip(),
                            description=f"Location: {loc}. {desc}",
                            pub_date=pub_date
                        ))
            else:
                print(f"❌ Remotive API returned HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Remotive fetch error: {e}")
            
        print(f"✅ Discovered {len(jobs)} verified software engineering jobs on Remotive!")
        return jobs

    async def fetch_jobs_async(self) -> List[JobListing]:
        return self.fetch_jobs()

if __name__ == "__main__":
    scraper = RemotiveScraper()
    jobs = scraper.fetch_jobs()
    for j in jobs[:5]:
        print(f"{j.company} - {j.title}: {j.link}")
