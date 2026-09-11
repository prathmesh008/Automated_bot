import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class MatchResult:
    answer: Optional[str]
    needs_review: bool
    reason: str

class QAMatcher:
    def __init__(self, bank_path="profile/screening_qa_bank.yaml"):
        self.bank_path = Path(bank_path)
        self.bank = self._load_bank()

    def _load_bank(self):
        with open(self.bank_path, "r") as f:
            data = yaml.safe_load(f)
            return data.get("questions", [])

    def match(self, label_text: str) -> MatchResult:
        """
        Takes an incoming label (e.g. 'Will you require sponsorship?')
        and checks the QA bank keywords to return the predefined answer.
        """
        label_lower = label_text.lower()
        for qa in self.bank:
            for keyword in qa.get("keywords", []):
                if keyword.lower() in label_lower:
                    return MatchResult(
                        answer=str(qa.get("answer")), 
                        needs_review=False, 
                        reason=f"Keyword match on '{keyword}'"
                    )
        
        # If no match found, it needs manual review
        return MatchResult(
            answer=None, 
            needs_review=True, 
            reason="No keywords matched in screening_qa_bank.yaml"
        )
