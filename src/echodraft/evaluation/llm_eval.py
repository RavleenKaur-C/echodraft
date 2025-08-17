from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

EVAL_PROMPT = """You are a strict writing evaluator.
Given a DRAFT and EXPECTATIONS, score the draft from 1–5 (integers) on:
- clarity
- style_fit (match to the requested style)
- completeness (does it meet the expectations)

Return ONLY valid JSON:
{
  "clarity": <1-5>,
  "style_fit": <1-5>,
  "completeness": <1-5>,
  "comments": "<one short paragraph>"
}

STYLE: {{ style }}
EXPECTATIONS:
\"\"\"{{ expectations }}\"\"\"

DRAFT:
\"\"\"{{ draft }}\"\"\"
"""

_llm_eval = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def evaluate_draft_llm(draft: str, style: str, expectations: str) -> Dict:
    prompt = PromptTemplate.from_template(EVAL_PROMPT, template_format="jinja2").format(
        style=style, expectations=expectations, draft=draft[:8000]
    )
    txt = _llm_eval.invoke(prompt).content.strip()
    # JSON parse as you already do...
    import json
    s, e = txt.find("{"), txt.rfind("}")
    payload = {"clarity":0,"style_fit":0,"completeness":0,"comments":"parse_error"}
    if s!=-1 and e!=-1 and e>s:
        try:
            payload = json.loads(txt[s:e+1])
        except Exception:
            pass
    return payload

