from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ..db import models
from ..db.database import get_db
from ..github_client import GitHubClient

router = APIRouter(prefix="/defects", tags=["defects"])


class RaiseDefectRequest(BaseModel):
    title: str
    description: str = ""
    slug: str | None = None


class DefectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_issue_number: int
    slug: str | None
    title: str
    status: str


@router.post("", response_model=DefectResponse)
def raise_defect(payload: RaiseDefectRequest, db: Session = Depends(get_db)):
    client = GitHubClient()
    issue_number = client.create_defect_issue(payload.title, payload.description)
    defect = models.Defect(
        github_issue_number=issue_number,
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        status="open",
    )
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return defect


@router.get("", response_model=list[DefectResponse])
def list_defects(db: Session = Depends(get_db)):
    return db.query(models.Defect).order_by(models.Defect.id.desc()).all()


@router.get("/{defect_id}", response_model=DefectResponse)
def get_defect(defect_id: int, db: Session = Depends(get_db)):
    return db.get(models.Defect, defect_id)
