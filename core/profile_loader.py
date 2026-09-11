"""
core/profile_loader.py

Loads the Knowledge Graph (profile/*.yaml) into a single flat object that
parsers (agent/parsers/*.py) read from directly. This replaces the
standalone `UserProfile` import the earlier greenhouse.py skeleton assumed
but never had wired up.

Two safety behaviors baked in, on purpose:

1. CRITICAL fields (name, email, phone) raise loudly if still "TODO" —
   these are needed for every application, so fail fast at startup rather
   than mid-run.
2. NON-critical fields (linkedin, github, portfolio, current_ctc) that are
   still "TODO" get silently converted to "" instead of being submitted
   verbatim to a real employer's form. A warning is logged either way —
   check `profile.load_warnings` before your first real run.
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple


PROFILE_DIR = Path("profile")
TODO_MARKER = "TODO"

CRITICAL_FIELDS = ["first_name", "last_name", "email", "phone"]


@dataclass
class Profile:
    full_name: str
    first_name: str
    last_name: str
    email: str
    phone: str
    location: str
    linkedin: str
    github: str
    portfolio: str

    citizenship: str
    requires_sponsorship: bool
    work_authorized_in: List[str]
    notice_period_days: int

    min_salary_inr_month: float
    expected_salary_inr_month: float
    current_ctc: Any

    experience: List[Dict]
    education: List[Dict]
    skills: List[Dict]

    resume_path: str = ""
    load_warnings: List[str] = field(default_factory=list)


def _load_yaml(filename: str) -> dict:
    with open(PROFILE_DIR / filename, "r") as f:
        return yaml.safe_load(f)


def _split_name(full_name: str) -> Tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _is_todo(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() == TODO_MARKER


def load_profile() -> Profile:
    identity = _load_yaml("identity.yaml")
    work_auth = _load_yaml("work_auth.yaml")
    comp = _load_yaml("compensation.yaml")
    exp = _load_yaml("experience.yaml")["experience"]
    edu = _load_yaml("education.yaml")["education"]
    skills = _load_yaml("skills_matrix.yaml")["skills"]

    first_name, last_name = _split_name(identity["name"])

    critical = {
        "first_name": first_name,
        "last_name": last_name,
        "email": identity["email"],
        "phone": identity["phone"],
    }
    missing_critical = [k for k, v in critical.items() if not v or _is_todo(v)]
    if missing_critical:
        raise ValueError(
            f"profile/identity.yaml has unresolved TODO(s) in critical field(s): "
            f"{missing_critical}. Fill these before running the bot — "
            f"they go into every single application."
        )

    warnings = []

    def clean(value, field_name):
        if _is_todo(value):
            warnings.append(field_name)
            return ""
        return value

    links = identity.get("links", {})

    return Profile(
        full_name=identity["name"],
        first_name=first_name,
        last_name=last_name,
        email=identity["email"],
        phone=identity["phone"],
        location=identity["location"],
        linkedin=clean(links.get("linkedin", ""), "identity.links.linkedin"),
        github=clean(links.get("github", ""), "identity.links.github"),
        portfolio=clean(links.get("portfolio", ""), "identity.links.portfolio"),
        citizenship=clean(work_auth.get("citizenship", ""), "work_auth.citizenship"),
        requires_sponsorship=work_auth["requires_sponsorship"],
        work_authorized_in=work_auth["work_authorized_in"],
        notice_period_days=work_auth["notice_period_days"],
        min_salary_inr_month=comp["min_salary_inr_month"],
        expected_salary_inr_month=comp["expected_salary_inr_month"],
        current_ctc=clean(comp.get("current_ctc", ""), "compensation.current_ctc"),
        experience=exp,
        education=edu,
        skills=skills,
        load_warnings=warnings,
    )


if __name__ == "__main__":
    p = load_profile()
    print(p)
    if p.load_warnings:
        print(f"\n⚠ {len(p.load_warnings)} field(s) still TODO, blanked out for safety: {p.load_warnings}")
