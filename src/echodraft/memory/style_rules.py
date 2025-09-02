import json, re
from pathlib import Path
from collections import Counter

RULES_PATH = Path.home()/".echodraft"/"style_rules.json"
RULES_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_RULES = {
    "bans": [  # phrases to remove
    ],
    "replacements": [  # list of {"from": "...", "to": "..."}
    ],
    "tone": {}  # reserved for future knobs (e.g., sentence length, voice)
}

def load_rules() -> dict:
    if RULES_PATH.exists():
        try:
            return json.loads(RULES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_RULES.copy()

def save_rules(rules: dict):
    RULES_PATH.write_text(json.dumps(rules, indent=2), encoding="utf-8")

def apply_rules_to_prompt(rules: dict) -> str:
    """Generate a compact instruction string usable in the draft prompt."""
    bans = rules.get("bans", [])
    repl = rules.get("replacements", [])
    lines = []
    if bans:
        lines.append("Avoid these phrases: " + "; ".join(f"“{b}”" for b in bans))
    if repl:
        lines.append("Make these substitutions: " + "; ".join(f"“{r['from']}”→“{r['to']}”" for r in repl))
    return "\n".join(lines) if lines else "None"

def update_rules_from_diffs(diffs: list[str]):
    """
    Very simple mining:
    - Deleted line that starts with a cliché → ban
    - Replacement patterns “We should”→“Let’s”, “In conclusion,” removed, etc.
    """
    rules = load_rules()
    bans = set(rules.get("bans", []))
    repl = {(r["from"], r["to"]) for r in rules.get("replacements", [])}

    # heuristic cues
    DELETE_CANDIDATES = ["in conclusion", "in summary", "we should", "i think", "it seems that"]
    for d in diffs:
        # diff lines like: "- In conclusion, ..." or "~ We should -> Let's"
        if d.startswith("- "):
            txt = d[2:].strip().lower()
            for cue in DELETE_CANDIDATES:
                if txt.startswith(cue):
                    bans.add(d[2:].strip())
        elif d.startswith("~ "):
            # format "~ FROM ==> TO"
            body = d[2:]
            if "==>" in body:
                frm, to = [x.strip() for x in body.split("==>", 1)]
                if frm and to and (frm, to) not in repl:
                    repl.add((frm, to))

    rules["bans"] = sorted(bans)
    rules["replacements"] = [{"from": f, "to": t} for (f, t) in sorted(repl)]
    save_rules(rules)
