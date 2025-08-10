from dataclasses import dataclass, field
from typing import List

@dataclass
class FeedbackExample:
    pattern: str
    replacement: str
    note: str = ""

@dataclass
class FeedbackStore:
    rules: List[FeedbackExample] = field(default_factory=list)

    def add(self, pattern: str, replacement: str, note: str = "") -> None:
        self.rules.append(FeedbackExample(pattern=pattern, replacement=replacement, note=note))

    def count(self) -> int:
        return len(self.rules)
