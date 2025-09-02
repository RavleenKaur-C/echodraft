from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from ..io.prompts import DRAFT_PROMPT, EXPLAIN_PROMPT, TRIAGE_PROMPT
import json
from .. import config
from ..memory.review_store import enqueue_review
from ..memory.style_rules import load_rules, apply_rules_to_prompt 

class DraftState(TypedDict, total=False):
    topic: str
    style: str
    words: int
    taboos: list[str]
    explain: bool
    draft: str
    explanation: str
    expectations: str  # <-- if not already present, add this to carry expectations

_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=500
)

def draft_node(state: DraftState) -> DraftState:
    rules = load_rules()
    personalization = apply_rules_to_prompt(rules)
    prompt = PromptTemplate.from_template(DRAFT_PROMPT).format(
        topic=state["topic"],
        style=state.get("style","professional"),
        words=state.get("words",220),
        taboos=", ".join(state.get("taboos", [])) or "None",
        expectations=state.get("expectations","") or "None",
        personalization=personalization,  
    )
    resp = _llm.invoke(prompt)
    return {"draft": resp.content.strip()}


def explain_node(state: DraftState) -> DraftState:
    if not state.get("explain"):
        return {"explanation": ""}
    resp = _llm.invoke(EXPLAIN_PROMPT)
    return {"explanation": resp.content.strip()}

_triage_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class TriageState(TypedDict, total=False):
    surface: str          # "email" | "notion" | "linkedin" | "blog"
    title: str
    metadata: dict
    content: str
    stale_days: int
    triage_label: str
    triage_reason: str
    triage_confidence: float
    # fields set by review node:
    review_required: bool
    review_id: str
    review_payload: str

def triage_node(state: TriageState) -> TriageState:
    prompt = PromptTemplate.from_template(TRIAGE_PROMPT).format(
        surface=state.get("surface","email"),
        title=state.get("title",""),
        metadata=json.dumps(state.get("metadata", {}))[:800],
        content=state.get("content","")[:8000],
        stale_days=state.get("stale_days", 30),
    )
    resp = _triage_llm.invoke(prompt).content.strip()
    start = resp.find("{"); end = resp.rfind("}")
    parsed = {"label": "REVIEW", "reason": "parse_error", "confidence": 0.0}
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(resp[start:end+1])
        except Exception:
            pass

    label = (parsed.get("label") or "REVIEW").upper()
    reason = parsed.get("reason", "")
    conf = float(parsed.get("confidence", 0))

    # --- heuristic fallback to improve NOTIFY recall ---
    text = f"{state.get('title','')} {state.get('content','')}".lower()
    notify_cues = [
        "fyi", "for your info", "no action required", "just sharing",
        "reminder", "outage resolved", "maintenance complete",
        "all hands", "policy update", "office will be closed", "oo o", "ooo", "out of office"
    ]
    if label == "IGNORE" and any(cue in text for cue in notify_cues):
        label = "NOTIFY"
        reason = "Heuristic: FYI/awareness cue detected; choose NOTIFY over IGNORE."
        conf = max(conf, 0.7)

    # guard unknown labels
    allowed = {"IGNORE","NOTIFY","DRAFT_EMAIL","DRAFT_NOTION","DRAFT_LINKEDIN","REVIEW"}
    if label not in allowed:
        label, reason, conf = "REVIEW", "Unknown label from model", 0.0

    return {"triage_label": label, "triage_reason": reason, "triage_confidence": conf}

REVIEW_CONF_THRESHOLD = getattr(config, "REVIEW_CONF_THRESHOLD", 0.5)

def review_node(state: TriageState | DraftState) -> TriageState:
    """Queue a human review task and return IDs so the CLI can list/approve."""
    triage = (state.get("triage_label") or "REVIEW").upper()
    reason = state.get("triage_reason","")
    conf = float(state.get("triage_confidence") or 0.0)

    payload = {
        "surface": state.get("surface"),
        "title": state.get("title"),
        "content": state.get("content"),
        "metadata": state.get("metadata", {}),
        "triage_label": triage,
        "triage_reason": reason,
        "triage_confidence": conf,
        "suggested_next": "draft" if triage in ("DRAFT_EMAIL","DRAFT_NOTION","DRAFT_LINKEDIN") else "ask",
        "topic": state.get("topic") or state.get("title") or "Untitled",
        "style": state.get("style","professional"),
        "words": state.get("words",220),
        "explain": state.get("explain", False),
    }
    rid = enqueue_review(payload)
    return {
        "review_required": True,
        "review_id": rid,
        "review_payload": json.dumps(payload),
        "draft": None,
        "explanation": f"Queued for human review (id={rid}). Reason: {reason} (conf={conf:.2f})"
    }