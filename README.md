# EchoDraft

EchoDraft is a **feedback-aware, style-learning writing co-pilot**. It learns from your edits,
mimics your tone, and gets better over time. Built with a modular graph so we can add
LangSmith evals, human-in-the-loop review, and memory step-by-step.
It is an ambient agent that will soon work with your email drafts, blog drafts, and bullet points
on Notion to give you a first draft of your thoughts without prompting, and then will allow you 
to iterate on it.

## Quickstart

```bash
# From the repo root
pip install -e .
cp .env.example .env   # keep real keys ONLY locally
echodraft draft --style professional --topic "Benefits of AI in education"
echodraft triage --surface notion --title "Proposal" --content "- Goals\n- Scope\n- TODO"
```

> The initial CLI works without any API keys. We'll wire models + LangGraph next.

## Roadmap (phased)
- [x] MVP CLI + modular layout
- [x] Agent graph (LangGraph) — triage → draft → explain → output
- [x] Triage node for selective drafting
- [ ] LangSmith tracing & simple eval set
- [ ] Human-in-the-loop review node
- [ ] Memory: line-level feedback (git-suggestion style)
- [ ] Memory: style-transfer via embeddings/RAG
- [ ] Integrations: Notion, Email, LinkedIn (publish/share)

## Contributing
- Put secrets in `.env` (never commit).
- Small PRs per feature (one node/feature per PR).
