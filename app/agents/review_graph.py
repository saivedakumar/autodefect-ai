from __future__ import annotations

from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from ..db import models
from ..db.database import SessionLocal
from ..github_client import GitHubClient
from .llm import ask_json
from .state import ReviewState

REVIEW_PROMPT = """You are an automated code reviewer for a defect-fix pull request.

Linked defect / issue context:
{issue_context}

Pull request diff:
{diff}

Review the diff for correctness, whether it plausibly fixes the described defect,
and any obvious bugs or regressions. Respond with ONLY a JSON object of the form:
{{"approve": true|false, "summary": "one paragraph summary", "comments": ["comment1", "comment2"]}}
"""


def fetch_diff(state: ReviewState) -> ReviewState:
    client = GitHubClient()
    diff = client.get_pr_diff(state["pr_number"])
    issue_number = client.get_linked_issue_number(state["pr_number"])
    issue_context = ""
    if issue_number:
        issue = client.repo.get_issue(issue_number)
        issue_context = f"#{issue_number} {issue.title}\n{issue.body or ''}"
    return {**state, "diff": diff, "issue_number": issue_number, "issue_context": issue_context}


def llm_review(state: ReviewState) -> ReviewState:
    result = ask_json(
        REVIEW_PROMPT.format(issue_context=state.get("issue_context", ""), diff=state["diff"])
    )
    verdict = "approve" if result.get("approve") else "request_changes"
    comments = "\n".join(result.get("comments", []))
    summary = result.get("summary", "")
    return {**state, "verdict": verdict, "comments": f"{summary}\n\n{comments}".strip()}


def post_review(state: ReviewState) -> ReviewState:
    client = GitHubClient()
    client.post_review(
        state["pr_number"],
        body=state["comments"] or "Automated review.",
        approve=state["verdict"] == "approve",
    )

    db = SessionLocal()
    try:
        pr_row = db.query(models.PullRequest).filter_by(github_pr_number=state["pr_number"]).first()
        if pr_row is None:
            defect = None
            if state.get("issue_number"):
                defect = (
                    db.query(models.Defect)
                    .filter_by(github_issue_number=state["issue_number"])
                    .first()
                )
            pr_row = models.PullRequest(
                github_pr_number=state["pr_number"],
                defect_id=defect.id if defect else None,
            )
            db.add(pr_row)
            db.flush()
        pr_row.review_verdict = state["verdict"]
        pr_row.status = "approved" if state["verdict"] == "approve" else "changes_requested"
        db.add(
            models.ReviewResult(
                pull_request_id=pr_row.id,
                verdict=state["verdict"],
                comments=state["comments"],
                model_used="deepseek-coder",
            )
        )
        db.commit()
    finally:
        db.close()
    return state


def merge_pr(state: ReviewState) -> ReviewState:
    client = GitHubClient()
    client.merge_pr(state["pr_number"])

    db = SessionLocal()
    try:
        pr_row = db.query(models.PullRequest).filter_by(github_pr_number=state["pr_number"]).first()
        if pr_row:
            pr_row.status = "merged"
            pr_row.merged_at = datetime.now(timezone.utc)
            if pr_row.defect:
                pr_row.defect.status = "merged"
            db.commit()
    finally:
        db.close()
    return state


def route_after_review(state: ReviewState) -> str:
    return "merge_pr" if state["verdict"] == "approve" else END


def build_review_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("fetch_diff", fetch_diff)
    graph.add_node("llm_review", llm_review)
    graph.add_node("post_review", post_review)
    graph.add_node("merge_pr", merge_pr)

    graph.set_entry_point("fetch_diff")
    graph.add_edge("fetch_diff", "llm_review")
    graph.add_edge("llm_review", "post_review")
    graph.add_conditional_edges("post_review", route_after_review, {"merge_pr": "merge_pr", END: END})
    graph.add_edge("merge_pr", END)
    return graph.compile()
