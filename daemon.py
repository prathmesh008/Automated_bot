import sys
import os

_venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    try:
        import playwright
    except ImportError:
        os.execv(_venv_python, [_venv_python] + sys.argv)

import asyncio
import time
import traceback
import random
from datetime import datetime
from run_daily import main as run_pipeline

async def run_24_7_daemon():
    print("🚀 Starting AI Job Bot 24/7 Daemon with Anti-Bot Jitter...")
    print("This script will wake up every 45-90 minutes to check for new jobs.")
    
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] Waking up to hunt for jobs...")
            
            # Execute the main pipeline
            await run_pipeline()
            
            # Anti-Bot Jitter: Sleep for 45 to 90 minutes randomly
            sleep_minutes = random.randint(45, 90)
            print(f"\n[{current_time}] Hunt complete. Jittering: Going back to sleep for {sleep_minutes} minutes...")
            await asyncio.sleep(sleep_minutes * 60)
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR in daemon loop: {type(e).__name__} - {e}")
            traceback.print_exc()
            print("Restarting in 5 minutes to recover from error...")
            await asyncio.sleep(300)

if __name__ == "__main__":
    try:
        asyncio.run(run_24_7_daemon())
    except KeyboardInterrupt:
        print("\nDaemon gracefully shut down by user.")
