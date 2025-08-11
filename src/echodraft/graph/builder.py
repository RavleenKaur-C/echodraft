from langgraph.graph import StateGraph, START, END
from .nodes import DraftState, draft_node, explain_node
from .nodes import TriageState, triage_node

# unified state = triage + draft
class EchoState(DraftState, TriageState, total=False):
    pass

def _route_after_triage(state: EchoState) -> str:
    label = (state.get("triage_label") or "").upper()
    if label in ("DRAFT_EMAIL", "DRAFT_NOTION", "DRAFT_LINKEDIN"):
        return "draft"
    if label in ("IGNORE", "NOTIFY"):
        return END
    return END  # REVIEW falls back to END for now (later: HITL)

def _route_after_draft(state: EchoState) -> str:
    return "explain" if state.get("explain") else END

def build_graph():
    g = StateGraph(EchoState)
    g.add_node("triage", triage_node)
    g.add_node("draft", draft_node)
    g.add_node("explain", explain_node)

    g.add_edge(START, "triage")
    g.add_conditional_edges("triage", _route_after_triage, {
        "draft": "draft",
        END: END
    })
    g.add_conditional_edges("draft", _route_after_draft, {
        "explain": "explain",
        END: END
    })
    g.add_edge("explain", END)
    return g.compile()
