from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agents.retest_graph import build_retest_graph
from ..db import models
from ..db.database import get_db
from ..github_client import GitHubClient
from ..security import require_service_token

router = APIRouter(prefix="/retests", tags=["retests"], dependencies=[Depends(require_service_token)])


class RunRetestRequest(BaseModel):
    pr_number: int


@router.post("/run")
def run_retest(payload: RunRetestRequest, db: Session = Depends(get_db)):
    client = GitHubClient()
    issue_number = client.get_linked_issue_number(payload.pr_number)
    if not issue_number:
        raise HTTPException(400, "PR does not reference a defect issue (expected 'Fixes #<n>')")

    defect = db.query(models.Defect).filter_by(github_issue_number=issue_number).first()
    if not defect:
        raise HTTPException(404, f"No defect found for issue #{issue_number}")

    graph = build_retest_graph()
    result = graph.invoke(
        {"defect_id": defect.id, "issue_number": issue_number, "pr_number": payload.pr_number}
    )
    return {"passed": result.get("passed"), "summary": result.get("ai_summary")}
