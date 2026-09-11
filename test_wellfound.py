import sys
import os

_venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    try:
        import playwright
    except ImportError:
        os.execv(_venv_python, [_venv_python] + sys.argv)

import asyncio
from agent.parsers.wellfound import apply_to_wellfound_job

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_url = sys.argv[1]
    else:
        print("Please provide a Wellfound Job URL.")
        print("Example: python test_wellfound.py 'https://wellfound.com/jobs/12345-software-engineer'")
        sys.exit(1)
        
    dummy_pitch = "Hi! I'm a fresher software engineer with 6 months of experience. I saw your listing perfectly matches my tech stack (Node.js/Python). I'd love to chat about how I can bring value to your engineering team."
    
    print(f"Testing Wellfound Parser on: {job_url}")
    asyncio.run(apply_to_wellfound_job(job_url, dummy_pitch, headless=False))
