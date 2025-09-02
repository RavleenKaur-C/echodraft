import json, os, time, uuid
from pathlib import Path
ROOT = Path.home()/".echodraft"/"review_queue"
ROOT.mkdir(parents=True, exist_ok=True)

def enqueue_review(payload: dict) -> str:
    rid = payload.get("id") or f"rvw_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    payload["id"] = rid
    path = ROOT/f"{rid}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return rid

def list_reviews():
    items = []
    for p in sorted(ROOT.glob("*.json")):
        try:
            items.append((p.stem, json.loads(p.read_text(encoding="utf-8"))))
        except Exception:
            pass
    return items

def load_review(rid: str) -> dict|None:
    p = ROOT/f"{rid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def delete_review(rid: str) -> bool:
    p = ROOT/f"{rid}.json"
    if p.exists():
        p.unlink()
        return True
    return False
