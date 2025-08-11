from textwrap import fill
from ..graph.builder import build_graph


STYLES = {
    "professional": ("clear, concise, structured", ["First, ", "Next, ", "Finally, "]),
    "persuasive": ("confident, benefit-led, action-oriented", ["Imagine this: ", "Here's why: ", "So what now? "]),
    "story": ("narrative, vivid, personal", ["A moment ago, ", "Then, ", "In the end, "]),
}

def _scaffold_paragraphs(topic: str, style_key: str, target_words: int) -> list[str]:
    tone, cues = STYLES.get(style_key, STYLES["professional"])
    approx_para = max(2, target_words // 90)
    parts = []
    cues_cycle = cues * ((approx_para // len(cues)) + 1)
    for i in range(approx_para):
        lead = cues_cycle[i]
        body = f"{lead}{topic} — written in a {tone} tone."
        parts.append(fill(body, width=88))
    return parts

def draft_text(topic: str, style: str="professional", target_words: int=220, explain: bool=False) -> str:
    app = build_graph()
    out = app.invoke({
        # triage inputs (for CLI we simulate a “content blob” to classify)
        "surface": "notion",
        "title": topic,
        "metadata": {},
        "content": f"- {topic}\n- key points:\n- TODO: expand into proposal",
        "stale_days": 30,
        # drafting inputs
        "topic": topic,
        "style": style,
        "words": target_words,
        "explain": explain
    })
    # If triage didn’t choose drafting, return reason.
    if out.get("triage_label") not in ("DRAFT_EMAIL","DRAFT_NOTION","DRAFT_LINKEDIN"):
        return f"[triage:{out.get('triage_label')}] {out.get('triage_reason','')}".strip()
    if explain and out.get("explanation"):
        return f'{out["draft"]}\n\n[why] {out["explanation"]}'
    return out["draft"]

def multi_draft_texts(topic: str, count: int = 3) -> list[str]:
    # quick loop with different styles; still uses the same graph
    styles = ["professional", "persuasive", "story"]
    results = []
    for i in range(count):
        results.append(draft_text(topic, style=styles[i % len(styles)], target_words=220, explain=False))
    return results
