"""
discovery/instahyre_scraper.py

Scraper for Instahyre — one of India's top startup job platforms.
Uses their public JSON API endpoint instead of scraping HTML for 100% reliability.
"""
import requests
from discovery.rss_poller import JobListing

class InstahyreScraper:
    def __init__(self, search_url=""):
        self.api_url = "https://www.instahyre.com/api/v1/job_search/?job_type=0"
        
    def fetch_jobs(self):
        print(f"🕵️‍♂️ Scraping Instahyre (via JSON API)")
        jobs = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
            response = requests.get(self.api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                objects = data.get('objects', [])
                
                for obj in objects[:50]: # Cap at 50
                    employer = obj.get('employer', {})
                    
                    title = obj.get('title') or obj.get('candidate_title')
                    company = employer.get('company_name')
                    job_id = obj.get('id')
                    
                    if title and company and job_id:
                        # Extract slug from public_url if present
                        public_url = obj.get('public_url', '')
                        link = public_url if public_url else f"https://www.instahyre.com/job-{job_id}/"
                        jobs.append(JobListing(
                            id=str(job_id),
                            title=title,
                            company=company,
                            link=link,
                            description=f"Skills: {', '.join(obj.get('keywords', []))}",
                            pub_date="Now"
                        ))
            else:
                print(f"❌ Instahyre API returned status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Instahyre Scraping Error: {e}")
            
        print(f"✅ Found {len(jobs)} jobs on Instahyre!")
        return jobs

    async def fetch_jobs_async(self):
        # Requests is blocking, but it's fast enough. Wrap in asyncio if needed, 
        # but for simplicity we can just return the sync call.
        return self.fetch_jobs()

if __name__ == "__main__":
    scraper = InstahyreScraper()
    jobs = scraper.fetch_jobs()
    for j in jobs:
        print(f"{j.company} - {j.title} - {j.link}")
