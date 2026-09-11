import asyncio
from agent.parsers.wellfound import apply_to_wellfound_job
from core.evaluator import evaluate_job
from core.profile_loader import load_profile

async def main():
    job_url = "https://wellfound.com/jobs/4420339-software-engineer-c"
    print("Generating dynamic pitch with Antigravity CLI...")
    
    profile = load_profile()
    eval = evaluate_job("Quantiq is a fast-growing startup building high-performance APIs and trading infrastructure in C++.", "Software Engineer (C++)", "Quantiq", profile)
    custom_pitch = eval.custom_pitch
    print(f"Generated Pitch:\n{custom_pitch}\n")
    
    print("Testing AI Form Filler on Quantiq...")
    await apply_to_wellfound_job(job_url, custom_pitch, headless=False)

if __name__ == "__main__":
    asyncio.run(main())
