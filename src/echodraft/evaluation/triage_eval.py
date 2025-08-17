import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Iterable, Dict, Tuple
from ..graph.builder import build_graph

LABELS = ["IGNORE","NOTIFY","DRAFT_EMAIL","DRAFT_NOTION","DRAFT_LINKEDIN","REVIEW"]

def _triage(app, item: dict) -> str:
    out = app.invoke({
        "surface": item["surface"],
        "title": item["title"],
        "content": item["content"],
        "metadata": {},
        "stale_days": 30,
        # dummy draft fields
        "topic": item.get("title",""),
        "style": "professional",
        "words": 150,
        "explain": False,
    })
    return (out.get("triage_label") or "REVIEW").upper()

def load_jsonl(path: str) -> Iterable[dict]:
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)

def _prf(tp, fp, fn):
    prec = tp/(tp+fp) if (tp+fp) else 0.0
    rec  = tp/(tp+fn) if (tp+fn) else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec) else 0.0
    return prec, rec, f1

def evaluate_triage(dataset_path: str) -> Dict:
    data = list(load_jsonl(dataset_path))
    app = build_graph()
    y_true, y_pred = [], []
    for ex in data:
        y_true.append(ex["label"].upper())
        y_pred.append(_triage(app, ex))

    # accuracy
    acc = sum(1 for t,p in zip(y_true,y_pred) if t==p)/len(y_true)

    # per-class
    per = {}
    cm = defaultdict(Counter)
    for t,p in zip(y_true,y_pred):
        cm[t][p] += 1
    for lbl in LABELS:
        tp = cm[lbl][lbl]
        fp = sum(cm[x][lbl] for x in LABELS if x!=lbl)
        fn = sum(cm[lbl][x] for x in LABELS if x!=lbl)
        prec, rec, f1 = _prf(tp, fp, fn)
        per[lbl] = {"precision": round(prec,3), "recall": round(rec,3), "f1": round(f1,3)}

    return {
        "size": len(y_true),
        "accuracy": round(acc,3),
        "per_label": per,
        "confusion": {k: dict(v) for k,v in cm.items()},
        "pred_counts": dict(Counter(y_pred)),
    }
