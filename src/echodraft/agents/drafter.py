from textwrap import fill

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

def draft_text(topic: str, style: str = "professional", target_words: int = 200, explain: bool = False) -> str:
    paras = _scaffold_paragraphs(topic, style, target_words)
    draft = "\n\n".join(paras)
    if explain:
        draft += "\n\n[why] Chose transitional cues and tone scaffold to match style preset."
    return draft

def multi_draft_texts(topic: str, count: int = 3) -> list[str]:
    keys = list(STYLES.keys())
    variants = []
    for i in range(count):
        style = keys[i % len(keys)]
        variants.append(draft_text(topic, style=style, target_words=220))
    return variants
