from typing import TypedDict


class ReviewState(TypedDict, total=False):
    pr_number: int
    issue_number: int | None
    diff: str
    issue_context: str
    verdict: str  # approve | request_changes
    comments: str


class RetestState(TypedDict, total=False):
    defect_id: int
    issue_number: int
    pr_number: int | None
    passed: bool
    report: str
    ai_summary: str
