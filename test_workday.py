import sys
import os

_venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    try:
        import playwright
    except ImportError:
        os.execv(_venv_python, [_venv_python] + sys.argv)

import asyncio
from agent.parsers.workday import apply_to_workday_job
from core.evaluator import evaluate_job
from core.profile_loader import load_profile

async def main():
    job_url = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/India-Pune/Software-Engineer_JR1985929"
    custom_pitch = "I am a backend engineer with strong experience in Node.js, Redis, and C++. I am deeply interested in NVIDIA's mission and would love the opportunity to contribute to your core engineering team."
    print(f"Direct Pitch: {custom_pitch}\n")
    print("Testing AI Form Filler on Workday...")
    await apply_to_workday_job(job_url, custom_pitch, headless=False)

if __name__ == "__main__":
    asyncio.run(main())
