from langgraph.graph import StateGraph, START, END
from .nodes import DraftState, draft_node, explain_node
from .nodes import TriageState, triage_node, review_node

# unified state = triage + draft
class EchoState(DraftState, TriageState, total=False):
    pass

def _route_after_triage(state: EchoState) -> str:
    label = (state.get("triage_label") or "").upper()
    conf = float(state.get("triage_confidence") or 0.0)
    # low-confidence or explicit REVIEW -> review lane
    if label in ("REVIEW",) or conf < 0.5:
        return "review"
    if label in ("DRAFT_EMAIL", "DRAFT_NOTION", "DRAFT_LINKEDIN"):
        return "draft"
    if label in ("IGNORE", "NOTIFY"):
        return END
    return "review"  # default safety

def _route_after_draft(state: EchoState) -> str:
    return "explain" if state.get("explain") else END

def build_graph():
    g = StateGraph(EchoState)
    g.add_node("triage", triage_node)
    g.add_node("review", review_node)     # NEW
    g.add_node("draft", draft_node)
    g.add_node("explain", explain_node)

    g.add_edge(START, "triage")
    g.add_conditional_edges("triage", _route_after_triage, {
        "review": "review",
        "draft": "draft",
        END: END
    })
    g.add_conditional_edges("draft", _route_after_draft, {
        "explain": "explain",
        END: END
    })
    g.add_edge("explain", END)
    g.add_edge("review", END)             
    return g.compile()
