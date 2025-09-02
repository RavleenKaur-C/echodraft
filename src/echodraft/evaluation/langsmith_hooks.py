import os
from contextlib import contextmanager
from datetime import datetime, timezone

RUNTIME_META = {
    "runtime": {
        "sdk": "langsmith-py",
        "library": "langsmith",
    },
    "metadata": {
        "revision_id": os.getenv("GIT_REV", "dirty"),
    },
}

try:
    from langsmith import Client
except Exception:
    Client = None


def _enabled() -> bool:
    return Client is not None and bool(os.getenv("LANGSMITH_API_KEY"))


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
    return _client


def _extract_run_id(run) -> str | None:
    if run is None:
        return None
    # SDK may return a Run pydantic model (has .id) or a dict
    rid = getattr(run, "id", None)
    if rid:
        return rid
    if isinstance(run, dict):
        return run.get("id") or run.get("run_id")
    return None


@contextmanager
def trace_run(name: str, tags=None, metadata=None, run_type: str = "chain"):
    """
    Wrap a CLI action as a top-level LangSmith run.
    - No-op if LANGSMITH_API_KEY not set or SDK not available.
    - Never throws; failures just skip tracing.
    """
    if not _enabled():
        yield None
        return

    client = _get_client()
    start = datetime.now(timezone.utc)

    # Create run (be permissive if the SDK changes again)
    run = None
    run_id = None
    try:
        inputs = {**(metadata or {})}
        extra = {**RUNTIME_META, **({"metadata": metadata} if metadata else {})}
        run = client.create_run(
            name=name,
            run_type=run_type,
            inputs=inputs,
            start_time=start,
            tags=(tags or []),
            extra=extra,
            # project auto-selected by LANGCHAIN_PROJECT env if set
        )
        run_id = _extract_run_id(run)
    except Exception:
        # Swallow tracing errors; proceed without tracing
        run_id = None

    status = "completed"
    error_payload = None
    try:
        yield run
    except Exception as e:
        status = "error"
        error_payload = {"message": str(e)}
        raise
    finally:
        if run_id:
            try:
                client.update_run(
                    run_id=run_id,
                    end_time=datetime.now(timezone.utc),
                    status=status,
                    error=error_payload,
                )
            except Exception:
                # Don’t let tracing break the CLI
                pass
