import json
import time
from typing import Dict, Iterable

from ..agents.drafter import draft_text
from .triage_eval import load_jsonl
from .llm_eval import evaluate_draft_llm
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from ..io.prompts import REFINE_PROMPT


# Deterministic, short responses for refinement
_refiner = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=600)

def eval_drafts_cli(
    dataset_path: str,
    words: int = 220,
    refine: bool = True,
    min_score: int = 4,
) -> str:
    data = list(load_jsonl(dataset_path))
    rows = []

    for ex in data:
        # 1) Generate the draft (pass expectations through so completeness improves)
        d = draft_text(
            topic=ex["topic"],
            style=ex.get("style", "professional"),
            target_words=words,
            explain=False,
            expectations=ex.get("expectations", "")
        )

        # 2) Score it with the LLM evaluator
        res = evaluate_draft_llm(
            draft=d,
            style=ex.get("reference_style", ex.get("style", "professional")),
            expectations=ex.get("expectations", "")
        )

        improved = False
        record: Dict = {
            "topic": ex["topic"],
            "style": ex.get("style", "professional"),
            "clarity": res.get("clarity", 0),
            "style_fit": res.get("style_fit", 0),
            "completeness": res.get("completeness", 0),
            "comments": (res.get("comments") or "")[:280],
        }

        # 3) Optional refinement pass if any score < threshold
        if refine and any(record[k] < min_score for k in ("clarity", "style_fit", "completeness")):
            rp = PromptTemplate.from_template(REFINE_PROMPT).format(
                expectations=ex.get("expectations", ""),
                comments=res.get("comments", ""),
                draft=d[:8000],
            )
            improved_text = _refiner.invoke(rp).content
            res2 = evaluate_draft_llm(
                draft=improved_text,
                style=ex.get("reference_style", ex.get("style", "professional")),
                expectations=ex.get("expectations", "")
            )
            record.update({
                "improved": True,
                "clarity2": res2.get("clarity", 0),
                "style_fit2": res2.get("style_fit", 0),
                "completeness2": res2.get("completeness", 0),
                "comments2": (res2.get("comments") or "")[:280],
            })
        else:
            record["improved"] = False

        rows.append(record)
        time.sleep(0.1)  # gentle pacing

    # 4) Summaries
    def avg(key: str):
        vals = [r[key] for r in rows if key in r]
        return round(sum(vals) / len(vals), 2) if vals else None

    summary = {
        "avg_clarity": avg("clarity"),
        "avg_style_fit": avg("style_fit"),
        "avg_completeness": avg("completeness"),
        "avg_clarity2": avg("clarity2"),
        "avg_style_fit2": avg("style_fit2"),
        "avg_completeness2": avg("completeness2"),
    }

    return json.dumps({"summary": summary, "results": rows}, indent=2)
