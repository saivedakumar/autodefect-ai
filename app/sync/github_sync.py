from ..db import models
from ..db.database import SessionLocal
from ..github_client import GitHubClient


def sync_defects() -> int:
    """Pull any GitHub issues labeled `defect` that aren't yet mirrored into SQLite."""
    client = GitHubClient()
    db = SessionLocal()
    synced = 0
    try:
        for issue in client.list_defect_issues(state="all"):
            defect = db.query(models.Defect).filter_by(github_issue_number=issue.number).first()
            if defect is None:
                db.add(
                    models.Defect(
                        github_issue_number=issue.number,
                        title=issue.title,
                        description=issue.body or "",
                        status="closed" if issue.state == "closed" else "open",
                    )
                )
                synced += 1
        db.commit()
    finally:
        db.close()
    return synced
