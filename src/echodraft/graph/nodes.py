from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from ..io.prompts import DRAFT_PROMPT, EXPLAIN_PROMPT, TRIAGE_PROMPT
import json
from .. import config

class DraftState(TypedDict, total=False):
    topic: str
    style: str
    words: int
    taboos: list[str]
    explain: bool
    draft: str
    explanation: str

_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=500  
)

def draft_node(state: DraftState) -> DraftState:
    prompt = PromptTemplate.from_template(DRAFT_PROMPT).format(
        topic=state["topic"],
        style=state.get("style","professional"),
        taboos=", ".join(state.get("taboos", [])) or "None",
        words=state.get("words", 220),
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

def triage_node(state: TriageState) -> TriageState:
    prompt = PromptTemplate.from_template(TRIAGE_PROMPT).format(
        surface=state.get("surface","email"),
        title=state.get("title",""),
        metadata=json.dumps(state.get("metadata", {}))[:800],
        content=state.get("content","")[:8000],
        stale_days=state.get("stale_days", 30),
    )
    resp = _triage_llm.invoke(prompt).content.strip()
    # be robust to stray text; find first {...}
    start = resp.find("{"); end = resp.rfind("}")
    parsed = {"label": "REVIEW", "reason": "parse_error", "confidence": 0.0}
    if start != -1 and end != -1 and end>start:
        try:
            parsed = json.loads(resp[start:end+1])
        except Exception:
            pass
    return {
        "triage_label": parsed.get("label","REVIEW"),
        "triage_reason": parsed.get("reason",""),
        "triage_confidence": float(parsed.get("confidence",0)),
    }