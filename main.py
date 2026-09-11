import os
import json
from core.parser import parse_resume
from core.evaluator import evaluate_job
from discovery.rss_poller import RSSPoller
from core.schema import UserProfile
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Please set GEMINI_API_KEY in .env file.")
        return

    # 1. Load or Parse Profile
    profile_path = "data/profile.json"
    profile = None
    
    if os.path.exists(profile_path):
        print("Loading existing profile...")
        with open(profile_path, 'r') as f:
            profile = UserProfile.model_validate_json(f.read())
    else:
        print("Parsing resume to create profile...")
        if os.path.exists("resume.txt"):
            profile = parse_resume("resume.txt", api_key)
            if profile:
                os.makedirs("data", exist_ok=True)
                with open(profile_path, 'w') as f:
                    f.write(profile.model_dump_json(indent=2))
                print("Profile saved to data/profile.json")
        else:
            print("No resume.txt found and no profile.json found.")
            return

    if not profile:
        print("Failed to create/load profile.")
        return

    # 2. Fetch Jobs
    print("\nFetching jobs from WeWorkRemotely...")
    poller = RSSPoller("https://weworkremotely.com/categories/remote-programming-jobs.rss")
    jobs = poller.fetch_jobs()
    
    # 3. Evaluate Top 3 Jobs
    print(f"\nEvaluating the 3 most recent jobs for {profile.name}...")
    for job in jobs[:5]:
        print(f"\n--- Evaluating: {job.title} at {job.company} ---")
        
        # Security/Blocklist Check
        if "urbanculture" in job.company.lower().replace(" ", "") or "urban culture" in job.company.lower():
            print(f">>> Action: Skipped. (Company matches blocked list: Urban Culture)")
            continue

        evaluation = evaluate_job(job.description, profile, api_key)
        
        if evaluation:
            print(f"Match Score: {evaluation.match_score}/100")
            print(f"Rationale: {evaluation.rationale}")
            print(f"Missing Skills: {', '.join(evaluation.missing_skills)}")
            print(f"Pitch: {evaluation.custom_pitch}")
            
            if evaluation.match_score >= 80:
                print(">>> Action: HIGH MATCH. Queuing for Agentic Application Engine...")
            else:
                print(">>> Action: Skip (Score below 80).")

if __name__ == "__main__":
    main()
