from dataclasses import dataclass, field

@dataclass
class UserProfile:
    taboo_phrases: list[str] = field(default_factory=lambda: ["In conclusion", "We should"])
    opening_pref: str = "bold"  # or "quote"

    def prefers_quote_open(self) -> bool:
        return self.opening_pref == "quote"
