from pydantic import BaseModel
from typing import List, Optional

class Experience(BaseModel):
    company: str
    title: str
    duration: str
    description: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    duration: str

class UserProfile(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    
    summary: str
    skills: List[str]
    experience: List[Experience]
    education: List[Education]
    
    # Preferences
    target_salary: str = "Min 40000 INR per month"
    experience_level: str = "Fresher / 6 months experience"
    
    # QA mapping for common behavioral/logistical questions
    # e.g., "Do you need sponsorship?": "No"
    qa_knowledge_base: dict[str, str] = {}
