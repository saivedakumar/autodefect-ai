from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from langgraph.graph import END, StateGraph

from ..config import get_settings
from ..db import models
from ..db.database import SessionLocal
from ..github_client import GitHubClient
from .llm import ask_json
from .state import RetestState

RETEST_PROMPT = """You are summarizing an automated Playwright test run that verifies a defect fix.

Pytest output:
{report}

Respond with ONLY a JSON object of the form:
{{"passed": true|false, "summary": "one paragraph, plain-English summary of the result"}}
"""


def run_playwright(state: RetestState) -> RetestState:
    settings = get_settings()
    test_dir = Path(settings.playwright_test_dir)

    db = SessionLocal()
    try:
        defect = db.get(models.Defect, state["defect_id"])
        slug = defect.slug if defect else None
    finally:
        db.close()

    target = [str(test_dir / f"test_{slug}.py")] if slug else [str(test_dir)]

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *target, "-v"],
        capture_output=True,
        text=True,
    )
    report = f"{proc.stdout}\n{proc.stderr}"
    return {**state, "passed": proc.returncode == 0, "report": report}


def llm_summarize(state: RetestState) -> RetestState:
    result = ask_json(RETEST_PROMPT.format(report=state["report"][-6000:]))
    summary = result.get("summary", "")
    # pytest's exit code is authoritative; the LLM summary can only agree with a
    # failure, never override a real failure into a pass.
    passed = state["passed"] and bool(result.get("passed", state["passed"]))
    return {**state, "ai_summary": summary, "passed": passed}


def record_and_close_or_reopen(state: RetestState) -> RetestState:
    client = GitHubClient()
    db = SessionLocal()
    try:
        defect = db.get(models.Defect, state["defect_id"])
        db.add(
            models.TestRun(
                defect_id=state["defect_id"],
                pull_request_id=None,
                passed=state["passed"],
                report=state["report"][-10000:],
                ai_summary=state["ai_summary"],
            )
        )
        if state["passed"]:
            client.close_issue(state["issue_number"], comment=f"AI retest passed:\n\n{state['ai_summary']}")
            defect.status = "closed"
        else:
            client.reopen_issue(state["issue_number"], comment=f"AI retest failed:\n\n{state['ai_summary']}")
            defect.status = "open"
        db.commit()
    finally:
        db.close()
    return state


def build_retest_graph():
    graph = StateGraph(RetestState)
    graph.add_node("run_playwright", run_playwright)
    graph.add_node("llm_summarize", llm_summarize)
    graph.add_node("record_and_close_or_reopen", record_and_close_or_reopen)

    graph.set_entry_point("run_playwright")
    graph.add_edge("run_playwright", "llm_summarize")
    graph.add_edge("llm_summarize", "record_and_close_or_reopen")
    graph.add_edge("record_and_close_or_reopen", END)
    return graph.compile()
