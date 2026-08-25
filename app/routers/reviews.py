from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..agents.review_graph import build_review_graph
from ..security import require_service_token

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(require_service_token)])


class RunReviewRequest(BaseModel):
    pr_number: int


@router.post("/run")
def run_review(payload: RunReviewRequest):
    graph = build_review_graph()
    result = graph.invoke({"pr_number": payload.pr_number})
    return {"verdict": result.get("verdict"), "comments": result.get("comments")}
