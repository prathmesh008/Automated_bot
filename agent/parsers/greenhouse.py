"""
agent/parsers/greenhouse.py

Platform-specific parser for Greenhouse-hosted applications
(boards.greenhouse.io/*). Greenhouse forms are templated across companies,
so field names are stable — this is far more reliable than generic
DOM-guessing, and doesn't need an LLM call for the standard fields.
"""

from playwright.async_api import Page
from core.qa_matcher import QAMatcher
from core.profile_loader import Profile
from agent.ai_form_filler import find_candidate_resume


STABLE_FIELD_MAP = {
    "first_name": 'input[name="job_application[first_name]"]',
    "last_name": 'input[name="job_application[last_name]"]',
    "email": 'input[name="job_application[email]"]',
    "phone": 'input[name="job_application[phone]"]',
}


async def fill_greenhouse_application(page: Page, profile: Profile, matcher: QAMatcher) -> dict:
    """
    Fills a Greenhouse application form with standard details, social links,
    screening questions, and attaches the candidate's resume.
    """
    review_queue = []

    # Wait for the Greenhouse form to render
    try:
        await page.wait_for_selector('input[name="job_application[first_name]"]', timeout=10000)
    except Exception:
        print("Could not find the Greenhouse form. The page might be broken or changed.")
        return {"auto_filled": 0, "needs_review": [{"question": "Form load", "reason": "Selector not found"}]}

    # 1. Fill stable, known fields directly
    for field, selector in STABLE_FIELD_MAP.items():
        locator = page.locator(selector)
        if await locator.count() > 0:
            val = getattr(profile, field, "")
            if val:
                await locator.fill(val)

    # 2. Fill standard social profiles / URLs if present on form
    social_mappings = [
        ('input[name*="linkedin"], input[id*="linkedin"], input[autocomplete*="linkedin"]', profile.linkedin),
        ('input[name*="github"], input[id*="github"]', profile.github),
        ('input[name*="website"], input[name*="portfolio"], input[id*="website"], input[id*="portfolio"]', profile.portfolio),
    ]
    for selector, value in social_mappings:
        if value:
            loc = page.locator(selector).first
            try:
                if await loc.count() > 0 and not await loc.input_value():
                    await loc.fill(value)
            except Exception:
                pass

    # 3. Attach candidate resume
    resume_path = find_candidate_resume(profile)
    if resume_path:
        file_input = page.locator('input[type="file"][name*="resume"], input[type="file"]').first
        if await file_input.count() > 0:
            print(f"   📎 Attaching resume to Greenhouse form: {resume_path}")
            try:
                await file_input.set_input_files(resume_path)
                print("   ✅ Resume attached successfully.")
            except Exception as e:
                print(f"   ⚠️ Could not attach resume to Greenhouse: {e}")

    # 4. Handle custom per-company questions
    custom_questions = page.locator('[id^="job_application_answers_attributes"]')
    count = await custom_questions.count()

    for i in range(count):
        block = custom_questions.nth(i)
        label_el = block.locator("label").first
        label_text = await label_el.inner_text() if await label_el.count() else ""
        if not label_text.strip():
            continue

        result = matcher.match(label_text)

        if result.needs_review or result.answer is None:
            review_queue.append({
                "question": label_text,
                "suggested_answer": result.answer,
                "reason": result.reason,
            })
            continue

        input_el = block.locator("input, select, textarea").first
        if await input_el.count() == 0:
            continue
            
        tag = await input_el.evaluate("el => el.tagName.toLowerCase()")

        try:
            if tag == "select":
                try:
                    await input_el.select_option(label=result.answer)
                except Exception:
                    await input_el.select_option(value=result.answer)
            elif await input_el.get_attribute("type") in ["checkbox", "radio"]:
                if str(result.answer).lower() in ["true", "yes", "1"]:
                    await input_el.check()
                else:
                    await input_el.uncheck()
            else:
                await input_el.fill(str(result.answer))
        except Exception as e:
            print(f"   ⚠️ Could not fill custom question '{label_text[:30]}': {e}")

    return {
        "auto_filled": count - len(review_queue),
        "needs_review": review_queue,
    }
