import sys
import os

_venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    try:
        import playwright
    except ImportError:
        os.execv(_venv_python, [_venv_python] + sys.argv)

import asyncio
from agent.parsers.yc import apply_to_yc_job
from core.profile_loader import load_profile
from core.evaluator import evaluate_job

if __name__ == "__main__":
    job_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.workatastartup.com/jobs/65805"
    profile = load_profile()
    
    simulated_job_desc = "We are looking for a founding engineer with strong Node.js, React, and AI experience to build the future of our product. Must be comfortable moving fast."
    
    print("🧠 Asking OpenAI to generate a tailored pitch...")
    evaluation = evaluate_job(simulated_job_desc, "Founding Engineer", "Y Combinator Startup", profile)
    real_ai_pitch = evaluation.custom_pitch
    print(f"\n--- AI GENERATED PITCH ---\n{real_ai_pitch}\n--------------------------\n")
    
    print(f"Testing Dedicated YC Parser on: {job_url}...")
    asyncio.run(apply_to_yc_job(job_url, custom_pitch=real_ai_pitch, headless=False))
