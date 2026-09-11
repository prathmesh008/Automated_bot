import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel
from typing import List

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    link: str
    description: str
    pub_date: str

class RSSPoller:
    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        
    def fetch_jobs(self) -> List[JobListing]:
        """Fetches and parses the RSS feed."""
        response = requests.get(self.feed_url)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        jobs = []
        
        for item in root.findall('./channel/item'):
            title_text = item.find('title').text if item.find('title') is not None else ""
            
            # WWR format: "Company: Title"
            company = "Unknown"
            title = title_text
            if ":" in title_text:
                company, title = title_text.split(":", 1)
                
            job = JobListing(
                id=item.find('guid').text if item.find('guid') is not None else item.find('link').text,
                title=title.strip(),
                company=company.strip(),
                link=item.find('link').text if item.find('link') is not None else "",
                description=item.find('description').text if item.find('description') is not None else "",
                pub_date=item.find('pubDate').text if item.find('pubDate') is not None else ""
            )
            jobs.append(job)
            
        return jobs

if __name__ == "__main__":
    # Example WWR Programming jobs RSS
    poller = RSSPoller("https://weworkremotely.com/categories/remote-programming-jobs.rss")
    jobs = poller.fetch_jobs()
    print(f"Found {len(jobs)} jobs.")
    if jobs:
        print(f"First job: {jobs[0].title} at {jobs[0].company}")
