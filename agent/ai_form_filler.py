import asyncio
import json
import re
import os
import subprocess
from dotenv import load_dotenv
from core.profile_loader import Profile
from playwright.async_api import Page

def find_candidate_resume(profile=None) -> str:
    """Locates candidate resume on disk (PDF preferred, then TXT/DOCX)."""
    candidates = [
        getattr(profile, "resume_path", None),
        os.path.expanduser("~/Downloads/side quest/ai_job_bot/resume.pdf"),
        os.path.expanduser("~/Downloads/side quest/ai_job_bot/resume.docx"),
        os.path.expanduser("~/Downloads/side quest/ai_job_bot/resume.txt"),
        "resume.pdf",
        "resume.txt"
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return ""

async def auto_fill_form_with_ai(page: Page, profile: Profile, custom_pitch: str = ""):
    """
    Uses OpenAI to analyze the application page, dynamically answer custom questions,
    attach candidate resume, and handle form inputs cleanly.
    """
    load_dotenv()
    resume_file = find_candidate_resume(profile)
    
    # 1. Extract the entire page text so the AI knows the context
    try:
        page_text = await page.evaluate("document.body.innerText")
    except Exception:
        page_text = ""
    
    # 2. Extract ALL form elements (including file inputs!)
    form_data_json = await page.evaluate("""
        () => {
            const elements = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]), select, textarea'));
            const formData = [];
            
            elements.forEach((el, index) => {
                if (el.offsetWidth === 0 && el.offsetHeight === 0 && el.type !== 'file') return;
                if (el.disabled) return;
                
                el.setAttribute('data-ai-index', index);
                let question = "";
                
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) question = label.innerText;
                }
                if (!question) {
                    const parentLabel = el.closest('label');
                    if (parentLabel) question = parentLabel.innerText;
                }
                if (!question) {
                    question = el.getAttribute('placeholder') || el.getAttribute('name') || "Unknown Field";
                }
                
                const fieldData = {
                    element_index: index,
                    tag_name: el.tagName.toLowerCase(),
                    type: el.getAttribute('type') || 'text',
                    question: question.trim(),
                    placeholder: el.getAttribute('placeholder') || ""
                };
                
                if (el.tagName.toLowerCase() === 'select') {
                    const options = Array.from(el.querySelectorAll('option')).map(o => o.innerText.trim());
                    fieldData.options = options.filter(o => o.length > 0);
                }
                formData.push(fieldData);
            });
            return JSON.stringify(formData);
        }
    """)
    
    fields = json.loads(form_data_json)
    if not fields:
        print("   No standard form fields found for AI to fill.")
        return
        
    print(f"🧠 AI Form Filler found {len(fields)} fields. Asking OpenAI (GPT-4o) how to answer them...")
    
    profile_skills = ", ".join([s.get('name', '') for s in profile.skills])
    profile_text = f"""
    Name: {profile.first_name} {profile.last_name}
    Email: {profile.email}
    Skills: {profile_skills}
    LinkedIn: {profile.linkedin}
    GitHub: {profile.github}
    Phone: {profile.phone}
    Location: {profile.location}
    """
    
    standard_bot_password = os.getenv("WORKDAY_PASSWORD", os.getenv("STANDARD_BOT_PASSWORD", "Prath@9968#Career"))
    
    prompt = f"""
You are an elite, highly professional Career Assistant and Job Applier acting on behalf of the candidate.
I have a web form for a job application with these fields:
{json.dumps(fields, indent=2)}

Candidate Profile:
{profile_text}

Context from the Job Page:
---
{page_text[:4000]}
---

Task:
You are applying for this job on candidate's behalf.
1. Answer all textual fields in the form accurately and persuasively in first person ("I").
2. If a field asks for a cover letter or a note to the hiring manager, use this exact pitch: "{custom_pitch}"
3. For dropdowns (including React Select text inputs), type the exact string of the option you want (e.g. "He/Him", "Wellfound"). Do NOT choose placeholder options like "-" or "Select...".
4. For phone numbers, output EXACTLY a 10-digit number without spaces, hyphens, or country codes (e.g., "9871057729").
5. If it asks for a resume upload, DO NOT create a file, just output the string "RESUME".
6. If a field asks you to create a password or log in, output: "{standard_bot_password}"
7. For checkboxes or radio buttons, output exactly "true" (to check) or "false" (to uncheck). Always check "Terms of Service" or agreement checkboxes.
8. If a field asks for a coding challenge file upload or a custom file, generate the raw code in `_files_to_create` and provide the absolute path as the field answer.

Return ONLY a valid JSON object matching this exact schema:
{{
  "answers": {{
    "0": "your answer for field 0"
  }},
  "_files_to_create": {{}}
}}
"""

    import openai
    client = openai.Client()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        result = json.loads(response.choices[0].message.content)
        answers = result.get("answers", {})
        
        # Create any files requested by the AI
        files_to_create = result.get("_files_to_create", {})
        for filepath, content in files_to_create.items():
            print(f"   📝 AI generated file: {filepath}")
            with open(filepath, "w") as f:
                f.write(content)
                
    except Exception as e:
        print(f"   ⚠️ OpenAI API parsing failed: {e}")
        return
        
    print("🤖 Filling fields with AI answers...")
    for field in fields:
        idx_str = str(field['element_index'])
        locator = page.locator(f"[data-ai-index='{idx_str}']")
        q_lower = field['question'].lower()
        
        # Check if field is resume upload
        if field['type'] == 'file' or any(k in q_lower for k in ['resume', 'cv', 'curriculum vitae']):
            if resume_file:
                print(f"   📎 Attaching candidate resume: {resume_file}")
                try:
                    await locator.set_input_files(resume_file)
                    print(f"   ✅ Resume uploaded for '{field['question'][:30]}'")
                except Exception as ex:
                    print(f"   ⚠️ Could not attach resume: {ex}")
            continue

        if idx_str in answers:
            val = answers[idx_str]
            if not val or val == "RESUME":
                continue
                
            try:
                if field['type'] == 'file':
                    print(f"   📎 Attaching file: {val}")
                    await locator.set_input_files(val)
                elif field['tag_name'] == 'select':
                    try:
                        await locator.select_option(label=str(val))
                    except Exception:
                        await locator.select_option(value=str(val))
                elif field['type'] in ['checkbox', 'radio']:
                    val_lower = str(val).lower()
                    if val_lower in ['true', 'yes', '1', 'on']:
                        await locator.check()
                    else:
                        await locator.uncheck()
                else:
                    await locator.fill(str(val))
                    el_id = await locator.get_attribute("id")
                    if el_id and "react-select" in el_id.lower():
                        await page.wait_for_timeout(500)
                        await page.keyboard.press("Enter")
                        
                print(f"   ✅ Answered '{field['question'][:30]}...' -> {str(val)[:30]}...")
            except Exception as e:
                print(f"   ⚠️ Could not fill field '{field['question'][:30]}': {e}")
