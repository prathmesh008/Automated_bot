import sys
import os

# Auto-bootstrap virtualenv if invoked via global python3
_venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    try:
        import playwright
    except ImportError:
        os.execv(_venv_python, [_venv_python] + sys.argv)

import asyncio
import re
from dotenv import load_dotenv
from core.evaluator import evaluate_job
from db.tracker import JobTracker
from agent.browser_agent import apply_to_job
from discovery.wellfound_scraper import WellfoundScraper
from discovery.instahyre_scraper import InstahyreScraper
from discovery.yc_scraper import YCScraper
from discovery.greenhouse_scraper import GreenhouseSearchScraper
from discovery.naukri_scraper import NaukriScraper
from discovery.remotive_scraper import RemotiveScraper
from discovery.himalayas_scraper import HimalayasScraper
from test_greenhouse import apply_to_greenhouse_job
from agent.parsers.wellfound import apply_to_wellfound_job
from agent.parsers.yc import apply_to_yc_job
from agent.parsers.lever import apply_to_lever_job

load_dotenv()

def get_platform_from_url(url: str) -> str:
    url_lower = url.lower()
    if "greenhouse.io" in url_lower:
        return "Greenhouse"
    elif "lever.co" in url_lower:
        return "Lever"
    elif "wellfound.com" in url_lower:
        return "Wellfound"
    elif "workatastartup.com" in url_lower or "ycombinator.com" in url_lower:
        return "YCombinator"
    elif "instahyre.com" in url_lower:
        return "Instahyre"
    elif "remotive.com" in url_lower:
        return "Remotive"
    elif "himalayas.app" in url_lower:
        return "Himalayas"
    elif "naukri.com" in url_lower:
        return "Naukri"
    return "Company Career Site"

async def main():
    print("=== 🚀 Starting Daily AI Job Application Loop ===")
    submit_applications = os.getenv("SUBMIT_APPLICATIONS", "false").lower() == "true"
    is_headless = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    mode_str = "PRODUCTION AUTO-SUBMIT" if submit_applications else "SAFE TEST / STAGING MODE (Submit Guarded)"
    print(f"🔧 Pipeline Mode: {mode_str} (Headless: {is_headless})")
    
    tracker = JobTracker()
    todays_count = tracker.get_todays_application_count()
    print(f"Jobs processed today: {todays_count} / 60")
    
    if todays_count >= 60:
        print("Daily limit reached (60/60). Sleeping until tomorrow.")
        return

    # 1. Load Profile
    from core.profile_loader import load_profile
    try:
        profile = load_profile()
    except Exception as e:
        print(f"Failed to load profile: {e}")
        return

    # 2. Fetch Jobs from High-Signal Startup Boards
    gh_url = "https://my.greenhouse.io/jobs/search?query=Software+Engineer&location=India"
    pollers = [
        RemotiveScraper(category="software-dev", limit=40),
        HimalayasScraper(limit=40),
        WellfoundScraper(search_url="https://wellfound.com/role/l/software-engineer/india"),
        InstahyreScraper(),
        YCScraper(),
        GreenhouseSearchScraper(search_url=gh_url),
        NaukriScraper(),
    ]
    
    all_jobs = []
    for poller in pollers:
        poller_name = poller.__class__.__name__
        try:
            if hasattr(poller, 'fetch_jobs_async'):
                jobs = await asyncio.wait_for(poller.fetch_jobs_async(), timeout=35)
            else:
                jobs = await asyncio.wait_for(asyncio.to_thread(poller.fetch_jobs), timeout=35)
            all_jobs.extend(jobs)
        except asyncio.TimeoutError:
            print(f"⚠️ {poller_name} timed out after 35s. Skipping to next board...")
        except Exception as e:
            print(f"⚠️ {poller_name} encountered error: {e}. Skipping to next board...")
        
    print(f"Discovered {len(all_jobs)} jobs across startup boards.")

    # 3. Evaluate & Apply
    for job in all_jobs:
        if tracker.get_todays_application_count() >= 60:
            print("Hit daily limit of 60! Stopping.")
            break
            
        # Security: Skip current employer
        if "urbanculture" in job.company.lower().replace(" ", "") or "urban culture" in job.company.lower():
            continue
            
        # Deduplication: Have we already applied to this?
        if tracker.has_applied_to(job.link):
            print(f"Skipping: Already applied to {job.title} at {job.company}.")
            continue
            
        # Cloudflare datacenter blocker: Skip Himalayas web URLs on cloud servers
        if "himalayas.app" in job.link:
            print(f"Skipping: {job.title} at {job.company} (Himalayas blocked by Cloudflare on datacenter IPs).")
            continue
            
        # Optimization: Pre-filter out clearly non-software roles and senior roles
        title_lower = job.title.lower()
        non_software_words = [
            "sales", "sdr", "bdr", "account executive", "marketing", "recruiter", 
            "hr ", "customer support", "customer success", "content", "copywriter", 
            "nurse", "medical", "accountant", "telecaller", "business development"
        ]
        if any(bad in title_lower for bad in non_software_words):
            print(f"\nSkipping: {job.title} at {job.company}")
            print("🔴 Pre-filtered (No API used): Non-software role.")
            continue

        senior_patterns = [
            r"\bsenior\b", r"\bsr\.?\b", r"\bstaff\b", r"\bprincipal\b", r"\bdirector\b", 
            r"\bhead of\b", r"\bvp\b", r"\btech lead\b", r"\blead engineer\b", 
            r"\bteam lead\b", r"\bengineering manager\b", r"\bproduct manager\b", r"\bgeneral manager\b"
        ]
        if any(re.search(pat, title_lower) for pat in senior_patterns):
            print(f"\nSkipping: {job.title} at {job.company}")
            print("🔴 Pre-filtered (No API used): Job title contains senior/management keywords.")
            continue

        print(f"\nEvaluating: {job.title} at {job.company}")
        
        full_text_to_evaluate = f"{job.title} {job.description}"
        evaluation = evaluate_job(full_text_to_evaluate, job.title, job.company, profile)
        
        if evaluation and evaluation.match_score >= 65:
            print(f"🟢 High Match ({evaluation.match_score}/100)! Pitching to {job.company}...")
            
            try:
                # Dynamically tailor resume for this specific job (Pratyush Narain 5 ATS rules)
                from core.resume_tailorer import tailor_resume_for_job
                try:
                    profile.resume_path = tailor_resume_for_job(job.title, job.company, full_text_to_evaluate, profile)
                except Exception as ex:
                    print(f"   ⚠️ Dynamic resume tailoring fallback: {ex}")

                # Route to the correct execution agent
                if "boards.greenhouse.io" in job.link:
                    print("🤖 Routing to deterministic Greenhouse Parser...")
                    await apply_to_greenhouse_job(job.link, headless=is_headless)
                elif "jobs.lever.co" in job.link or "lever.co" in job.link:
                    print("🤖 Routing to deterministic Lever Parser...")
                    await apply_to_lever_job(job.link, evaluation.custom_pitch, headless=is_headless)
                elif "wellfound.com" in job.link:
                    print("🤖 Routing to native Wellfound Parser...")
                    await apply_to_wellfound_job(job.link, evaluation.custom_pitch, headless=is_headless)
                elif "workatastartup.com" in job.link:
                    print("🤖 Routing to native YC Parser...")
                    await apply_to_yc_job(job.link, evaluation.custom_pitch, headless=is_headless)
                elif "instahyre.com" in job.link:
                    from agent.parsers.instahyre import apply_to_instahyre_job
                    await apply_to_instahyre_job(job.link, evaluation.custom_pitch, headless=is_headless)
                elif "myworkdayjobs.com" in job.link:
                    from agent.parsers.workday import apply_to_workday_job
                    print("🤖 Routing to native Workday Parser with IMAP Auto-Registrar...")
                    await apply_to_workday_job(job.link, evaluation.custom_pitch, headless=is_headless)
                else:
                    print(f"🤖 Routing to generic Playwright agent for company site: {job.link}...")
                    res = await apply_to_job(job.link, evaluation.custom_pitch)
                    if res and res.get("status") not in ["success", "staged_for_review"]:
                        raise Exception("Generic agent could not complete form submission.")
                
                # 5. Track application
                tracker.log_application(
                    company=job.company, 
                    title=job.title, 
                    platform=get_platform_from_url(job.link), 
                    url=job.link, 
                    score=evaluation.match_score,
                    job_description=getattr(job, "description", ""),
                    match_rationale=getattr(evaluation, "rationale", ""),
                    custom_pitch=getattr(evaluation, "custom_pitch", ""),
                    tailored_resume_path=getattr(profile, "resume_path", ""),
                    location=getattr(job, "location", ""),
                    status="Applied" if submit_applications else "Staged"
                )
                tag = "SUBMITTED" if submit_applications else "STAGED (TEST MODE)"
                print(f"✅ [{tag}] Logged {job.company} ({job.title}) in tracker!")
            except Exception as e:
                print(f"❌ Failed to process application for {job.company}: {e}")
                tracker.log_failure(
                    company=job.company,
                    title=job.title,
                    platform=get_platform_from_url(job.link),
                    url=job.link,
                    error_message=str(e)
                )
                if sys.platform == "darwin":
                    os.system(f'osascript -e \'display notification "{alert_msg}" with title "AI Job Bot Alert"\'')
                print(f"📣 Logged manual review alert for: {job.link}")
        else:
            score = evaluation.match_score if evaluation else 0
            print(f"🔴 Skipped (Score: {score}). {evaluation.rationale if evaluation else ''}")

    # End-of-run summary
    stats = tracker.get_todays_stats()
    print(f"\n{'='*50}")
    print("📊 Daily Summary:")
    print(f"   ✅ Processed today: {stats['applied_today']}")
    print(f"   ❌ Failed today: {stats['failed_today']}")
    print(f"   📦 Total all-time: {stats['total_all_time']}")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
