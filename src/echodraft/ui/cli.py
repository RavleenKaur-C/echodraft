import typer
from typing import Optional
from ..agents.drafter import draft_text, multi_draft_texts
from ..agents.reviser import revise_text
from ..evaluation.metrics import summarize_metrics
from ..evaluation.langsmith_hooks import trace_run
import sys


app = typer.Typer(help="EchoDraft CLI — draft, revise, and track improvements")

@app.command()
def draft(topic: str = typer.Option(..., help="What to write about"),
          style: str = typer.Option("professional", help="Style preset (professional/persuasive/story)"),
          words: int = typer.Option(200, help="Target word count"),
          explain: bool = typer.Option(False, help="Show reasoning for certain choices")):
    """Generate a first draft."""
    with trace_run("draft", tags=["cli","phase3"], metadata={"topic": topic, "style": style, "words": words, "explain": explain}):
        result = draft_text(topic=topic, style=style, target_words=words, explain=explain)
        typer.echo(result)

@app.command("multi-draft")
def multi_draft(topic: str = typer.Option(..., help="What to write about"),
                count: int = typer.Option(3, help="Number of variants")):
    """Generate multiple draft variants."""
    with trace_run("multi-draft", tags=["cli","phase3"], metadata={"topic": topic, "count": count}):
        variants = multi_draft_texts(topic=topic, count=count)
        for i, v in enumerate(variants, 1):
            typer.echo(f"\n=== Variant {i} ===\n{v}\n")
    
@app.command()
def revise(file: str = typer.Argument(..., help="Path to a text file to revise"),
           feedback: str = typer.Option(..., help="Short feedback, e.g., 'too formal, add example'")):
    """Revise an existing draft using feedback."""
    with trace_run("revise", tags=["cli","phase3"], metadata={"file": file, "feedback": feedback[:120]}):
        with open(file, "r", encoding="utf-8") as f:
            original = f.read()
        revised = revise_text(original, feedback)
        typer.echo(revised)

@app.command()
def metrics():
    """Show improvement metrics (stub until LangSmith wired)."""
    with trace_run("metrics", tags=["cli","phase3"]):
        typer.echo(summarize_metrics())

@app.command()
def triage(
    surface: str = typer.Option("notion", help="email|notion|linkedin|blog"),
    title: str = typer.Option("", help="Title/subject"),
    content: str = typer.Option("", help="Raw content/body to classify"),
    stale_days: int = typer.Option(30, help="Age threshold in days"),
):
    """Run triage only and print the label, reason, confidence."""
    from ..graph.builder import build_graph
    with trace_run("triage", tags=["cli","phase3"], metadata={"surface": surface, "title": title, "stale_days": stale_days}):
        appg = build_graph()
        out = appg.invoke({
            "surface": surface,
            "title": title,
            "content": content,
            "metadata": {},
            "stale_days": stale_days,
            # dummy draft fields to keep state happy
            "topic": title or "Untitled",
            "style": "professional",
            "words": 200,
            "explain": False,
        })
        label = (out.get("triage_label") or "").upper()
        reason = out.get("triage_reason", "")
        conf = out.get("triage_confidence", 0)
        typer.echo(f"label={label}  confidence={conf:.2f}")
        if reason:
            typer.echo(f"reason: {reason}")

@app.command("eval-triage")
def eval_triage(dataset: str = typer.Option("datasets/triage.jsonl", help="Path to triage dataset JSONL")):
    """Evaluate triage accuracy/metrics on a labeled dataset."""
    from ..evaluation.run_eval import eval_triage_cli
    with trace_run("eval-triage", tags=["cli","phase3"], metadata={"dataset": dataset}):
        typer.echo(eval_triage_cli(dataset))

@app.command("eval-drafts")
def eval_drafts(
    dataset: str = typer.Option("datasets/drafts.jsonl", help="Path to drafts dataset JSONL"),
    words: int = typer.Option(220, help="Target word count for generated drafts"),
    refine: bool = typer.Option(True, help="Auto-refine drafts that score below threshold"),
    min_score: int = typer.Option(4, help="Refine if any score < min_score"),
):
    """LLM-based evaluation of generated drafts (clarity, style-fit, completeness) with optional auto-refine."""
    from ..evaluation.run_eval import eval_drafts_cli
    with trace_run("eval-drafts", tags=["cli","phase3"], metadata={
        "dataset": dataset, "words": words, "refine": refine, "min_score": min_score
    }):
        typer.echo(eval_drafts_cli(dataset, words, refine, min_score))

@app.command("review-queue")
def review_queue():
    """List queued human reviews."""
    from ..memory.review_store import list_reviews
    items = list_reviews()
    if not items:
        typer.echo("No review tasks.")
        return
    for rid, payload in items:
        label = payload.get("triage_label")
        title = payload.get("title","")
        conf = payload.get("triage_confidence",0)
        typer.echo(f"{rid}  [{label} conf={conf:.2f}]  {title}")

@app.command("review-approve")
def review_approve(
    rid: str = typer.Argument(..., help="Review id from review-queue"),
    answer: str = typer.Option("", help="Optional answer/context to unblock drafting"),
    notes: str = typer.Option("", help="Optional reviewer notes"),
):
    """Approve a review task and continue drafting with the provided answer/context."""
    from ..memory.review_store import load_review, delete_review
    from ..agents.drafter import draft_text
    payload = load_review(rid)
    if not payload:
        typer.echo(f"Review id not found: {rid}")
        raise typer.Exit(code=1)

    topic = payload.get("title") or payload.get("topic") or "Untitled"
    style = payload.get("style","professional")
    exp = ""
    if answer:
        exp = f"Reviewer answer/context to incorporate: {answer}"
        if notes:
            exp += f" | Reviewer notes: {notes}"

    out = draft_text(topic=topic, style=style, target_words=payload.get("words",220), explain=False, expectations=exp)
    ok = delete_review(rid)
    if ok:
        typer.echo(f"[approved] {rid}\n")
    typer.echo(out)

@app.command("learn-edits")
def learn_edits(
    original: str = typer.Argument(..., help="Path to ORIGINAL draft file"),
    edited: str = typer.Argument(..., help="Path to EDITED draft file"),
):
    """Learn from line-level edits and update style rules (bans/replacements)."""
    from ..memory.diff_utils import line_level_diff
    from ..memory.style_rules import update_rules_from_diffs, load_rules, apply_rules_to_prompt
    with open(original, "r", encoding="utf-8") as f:
        o = f.read()
    with open(edited, "r", encoding="utf-8") as f:
        e = f.read()
    diffs = line_level_diff(o, e)
    update_rules_from_diffs(diffs)
    rules = load_rules()
    typer.echo("Learned from edits. Current personalization rules:\n")
    result = (apply_rules_to_prompt(rules))
    sys.stdout.write(result + "\n")
