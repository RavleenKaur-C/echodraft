from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

REVISE_PROMPT = """You are a careful rewrite assistant.
Revise the draft based on the FEEDBACK. Follow these rules:
- Apply feedback faithfully (tone, brevity, clarity).
- Preserve structure and Markdown formatting (headings, lists, signatures).
- Do NOT leave incomplete sentences or placeholders.
- Return ONLY the full revised draft (no preamble, no commentary).

FEEDBACK:
"{feedback}"

DRAFT:
<<<
{draft}
>>>"""

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4, max_tokens=700)

def revise_text(draft: str, feedback: str) -> str:
    prompt = PromptTemplate.from_template(REVISE_PROMPT).format(
        feedback=feedback, draft=draft
    )
    resp = _llm.invoke(prompt)
    return resp.content.strip()
