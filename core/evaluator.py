import re
from pydantic import BaseModel, Field
from typing import Optional, List
from core.profile_loader import Profile

class JobEvaluation(BaseModel):
    match_score: int = Field(description="A score from 0 to 100 indicating how well the profile matches the job.")
    rationale: str = Field(description="A short explanation for the match score.")
    missing_skills: List[str] = Field(description="Key skills required by the job but missing from the profile.")
    custom_pitch: Optional[str] = Field(description="A short, tailored 2-3 sentence pitch to the founder/hiring manager based on the job and profile.")

DISQUALIFIED_KEYWORDS = [
    "sales", "sdr", "bdr", "account executive", "inside sales", "outside sales",
    "telecaller", "business development", "marketing", "seo", "growth marketer",
    "recruiter", "talent acquisition", "hr ", "human resources", "payroll",
    "customer support", "customer service", "customer success", "support specialist",
    "content writer", "copywriter", "journalist", "medical", "nurse", "clinical",
    "accountant", "bookkeeper", "tax", "auditor", "legal", "paralegal", "attorney",
    "real estate", "underwriter", "loan officer", "insurance agent"
]

PRIMARY_TARGET_ROLES = [
    "software engineer", "software developer", "sde", "full stack", "fullstack",
    "backend", "frontend", "ai engineer", "ai software", "ml engineer", 
    "founding engineer", "founding software", "associate software", "junior software",
    "node", "python developer", "python engineer", "react developer", "web developer",
    "systems engineer", "cloud engineer", "devops engineer"
]

REQUIRED_TECH_ROLES = [
    "software", "developer", "engineer", "programmer", "backend", "full stack",
    "fullstack", "frontend", "web dev", "ai ", "ai/", "ai-", "ml ", "ml/", "ml-",
    "machine learning", "deep learning", "llm", "genai", "computer vision", "nlp",
    "devops", "cloud", "sre", "site reliability", "infrastructure", "platform engineer",
    "data engineer", "data platform", "node", "python", "react", "c++", "golang", "systems"
]

def evaluate_job(job_description: str, job_title: str, company_name: str, profile: Profile, api_key: str = None) -> JobEvaluation:
    title_lower = job_title.lower()
    desc_lower = job_description.lower()
    combined_lower = f"{title_lower} {desc_lower}"
    
    # 1. Immediate Disqualification for Non-Tech Roles
    for bad_word in DISQUALIFIED_KEYWORDS:
        if re.search(rf"\b{re.escape(bad_word)}\b", title_lower):
            return JobEvaluation(
                match_score=0,
                rationale=f"Disqualified: Non-software role detected in title ('{bad_word}').",
                missing_skills=[],
                custom_pitch=None
            )
            
    # 2. Require Software / Engineering role alignment in Title
    has_tech_title = any(role in title_lower for role in REQUIRED_TECH_ROLES)
    if not has_tech_title:
        tech_indicators = ["git", "api", "database", "sql", "backend", "frontend", "docker", "python", "javascript", "typescript", "c++"]
        tech_count = sum(1 for t in tech_indicators if re.search(rf"\b{t}\b", desc_lower))
        if tech_count < 3:
            return JobEvaluation(
                match_score=0,
                rationale="Disqualified: Role title does not match software/engineering.",
                missing_skills=[],
                custom_pitch=None
            )

    # 3. Dynamic Score Calculation
    # If the title is explicitly a primary target role (e.g. Software Engineer, Backend, Full Stack),
    # start at 70 so listing-page scrapes with brief descriptions are not discarded.
    if any(target in title_lower for target in PRIMARY_TARGET_ROLES):
        match_score = 70
    else:
        match_score = 45

    found_skills = []
    for skill_dict in profile.skills:
        skill_name = skill_dict.get("name", "")
        if skill_name and re.search(rf"\b{re.escape(skill_name.lower())}\b", combined_lower):
            match_score += 10
            found_skills.append(skill_name)
            
    # Tech stack bonuses for candidate's core competencies:
    core_stack = ["node", "python", "react", "next.js", "redis", "mongodb", "fastapi", "ai", "llm", "rag", "docker", "c++"]
    core_matches = [c for c in core_stack if re.search(rf"\b{re.escape(c)}\b", combined_lower)]
    if len(core_matches) >= 2:
        match_score += 10

    # Early-career / Fresher bonus
    early_career_keywords = ["fresher", "junior", "entry level", "entry-level", "intern", "0-1", "0-2", "early career", "associate"]
    if any(k in combined_lower for k in early_career_keywords):
        match_score += 10

    match_score = min(match_score, 95)
    
    custom_pitch = f"I am a software engineer with strong hands-on experience in {', '.join(found_skills[:3]) if found_skills else 'backend and full-stack systems'}. Your work at {company_name} aligns directly with my background, and I would love to contribute to your engineering team."
    
    # 4. Generate high-quality personalized pitch with GPT-4o-mini if high match
    if match_score >= 65:
        try:
            import os
            import json
            import openai
            
            client = openai.Client(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""You are {profile.first_name} {profile.last_name}, a passionate Software Engineer applying for the {job_title} role at {company_name}.
Job description / context:
---
{job_description[:3000]}
---

Candidate background:
Name: {profile.full_name}
Experience: {', '.join([exp.get('company', '') for exp in profile.experience])}
Core Tech: Node.js, Next.js, Redis, MongoDB, Python, Docker, LLMs/RAG

Write a concise, deeply technical 2-paragraph note to the founder or engineering hiring manager.
1. Highlight specific technical challenges mentioned in the job and relate them to your experience with high-throughput backends, caching (Redis), distributed task queues, or full-stack delivery.
2. Be authentic, confident, and professional. Do not start with generic pleasantries like "Dear Hiring Manager" or "My name is...". Speak as an engineer ready to ship code.

Return ONLY a JSON object:
{{
    "custom_pitch": "your pitch string here"
}}"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            if "custom_pitch" in result:
                custom_pitch = result["custom_pitch"]
            
        except Exception as e:
            print(f"⚠️ Pitch generation notice: {e}")
            
    return JobEvaluation(
        match_score=match_score,
        rationale=f"Software Role Match: Found relevant stack ({', '.join(found_skills[:4]) if found_skills else 'Core Software Engineer'}).",
        missing_skills=[],
        custom_pitch=custom_pitch
    )
