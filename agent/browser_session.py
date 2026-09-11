"""
agent/browser_session.py

Shared browser session manager. Opens Chrome ONCE and reuses the same
browser context across all parsers. This is:
1. Much faster (no 3-5 sec startup per job)
2. Less suspicious (one browser session, not 60 separate launches)
3. Easier on MacBook Air resources
"""
import os
from playwright.async_api import async_playwright, BrowserContext

_context: BrowserContext = None
_playwright = None

BOT_PROFILE_DIR = os.path.expanduser("~/Downloads/side quest/ai_job_bot/chrome_profile")

async def get_browser() -> BrowserContext:
    """Returns a shared, persistent browser context. Creates one if it doesn't exist."""
    global _context, _playwright
    
    if _context is None:
        _playwright = await async_playwright().start()
        _context = await _playwright.chromium.launch_persistent_context(
            user_data_dir=BOT_PROFILE_DIR,
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        print("🌐 Shared browser session started.")
    
    return _context

async def close_browser():
    """Closes the shared browser session. Call this at the end of the pipeline."""
    global _context, _playwright
    
    if _context:
        await _context.close()
        _context = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
        print("🌐 Shared browser session closed.")

async def new_page():
    """Opens a new tab in the shared browser."""
    ctx = await get_browser()
    return await ctx.new_page()
