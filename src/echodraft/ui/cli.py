import typer
from typing import Optional
from ..agents.drafter import draft_text, multi_draft_texts
from ..agents.reviser import revise_text
from ..evaluation.metrics import summarize_metrics

app = typer.Typer(help="EchoDraft CLI — draft, revise, and track improvements")

@app.command()
def draft(topic: str = typer.Option(..., help="What to write about"),
          style: str = typer.Option("professional", help="Style preset (professional/persuasive/story)"),
          words: int = typer.Option(200, help="Target word count"),
          explain: bool = typer.Option(False, help="Show reasoning for certain choices")):
    """Generate a first draft."""
    result = draft_text(topic=topic, style=style, target_words=words, explain=explain)
    typer.echo(result)

@app.command("multi-draft")
def multi_draft(topic: str = typer.Option(..., help="What to write about"),
                count: int = typer.Option(3, help="Number of variants")):
    """Generate multiple draft variants."""
    variants = multi_draft_texts(topic=topic, count=count)
    for i, v in enumerate(variants, 1):
        typer.echo(f"\n=== Variant {i} ===\n{v}\n")
    
@app.command()
def revise(file: str = typer.Argument(..., help="Path to a text file to revise"),
           feedback: str = typer.Option(..., help="Short feedback, e.g., 'too formal, add example'")):
    """Revise an existing draft using feedback."""
    with open(file, "r", encoding="utf-8") as f:
        original = f.read()
    revised = revise_text(original, feedback)
    typer.echo(revised)

@app.command()
def metrics():
    """Show improvement metrics (stub until LangSmith wired)."""
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