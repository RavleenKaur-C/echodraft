import re
from textwrap import fill

# Very simple 'feedback-aware' rewrite rules (will be replaced by agent logic later)
RULES = {
    "too formal": [
        (re.compile(r"\bhowever\b", re.I), "but"),
        (re.compile(r"\bthus\b", re.I), "so"),
    ],
    "add example": [
        (re.compile(r"$", re.M), "\nFor example, consider a simple case that illustrates the point."),
    ],
    "shorten": [
        (re.compile(r"\s+\S+\s*$", re.M), "."),  # naive trim
    ],
}

def revise_text(text: str, feedback: str) -> str:
    fb = feedback.lower()
    for key, rules in RULES.items():
        if key in fb:
            for pat, repl in rules:
                text = pat.sub(repl, text)
    # Basic tightening: collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return fill(text, width=88)
