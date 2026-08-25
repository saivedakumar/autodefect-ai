"""End-to-end walk through Raise Defect -> AI Reviews PR -> Merge -> AI Retests
-> Close Defect, driven entirely through the real FastAPI app and the real
LangGraph agents. GitHub and Ollama are replaced with fakes so this proves the
pipeline's own wiring/logic is correct without needing a live token, a running
Ollama, or a self-hosted runner.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db.database import Base, get_db
from app.main import app

SERVICE_TOKEN_HEADER = {"X-Service-Token": get_settings().service_token}


class FakeIssue:
    def __init__(self, number: int) -> None:
        self.number = number
        self.title = f"fake issue {number}"
        self.body = "fake body"


class FakeRepo:
    def __init__(self) -> None:
        self._issues: dict[int, FakeIssue] = {}

    def get_issue(self, number: int) -> FakeIssue:
        return self._issues.setdefault(number, FakeIssue(number))


class FakeGitHubClient:
    """Stands in for the real GitHub API so the loop runs with no token/network."""

    _issue_counter = [1000]
    pr_to_issue: dict[int, int] = {}
    calls: list[tuple] = []
    repo = FakeRepo()

    def create_defect_issue(self, title: str, body: str) -> int:
        FakeGitHubClient._issue_counter[0] += 1
        return FakeGitHubClient._issue_counter[0]

    def get_pr_diff(self, pr_number: int) -> str:
        return "--- demo_app/main.py (+3/-3)\n+ if not title.strip(): return"

    def get_linked_issue_number(self, pr_number: int) -> int | None:
        return FakeGitHubClient.pr_to_issue.get(pr_number)

    def post_review(self, pr_number: int, body: str, approve: bool) -> None:
        FakeGitHubClient.calls.append(("post_review", pr_number, approve))

    def merge_pr(self, pr_number: int) -> None:
        FakeGitHubClient.calls.append(("merge_pr", pr_number))

    def close_issue(self, number: int, comment: str | None = None) -> None:
        FakeGitHubClient.calls.append(("close_issue", number))

    def reopen_issue(self, number: int, comment: str | None = None) -> None:
        FakeGitHubClient.calls.append(("reopen_issue", number))


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


@pytest.fixture()
def client(monkeypatch):
    # One shared in-memory SQLite connection for the whole test, standing in
    # for the on-disk autodefect.db so nothing here touches the real dev DB.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # The LangGraph nodes open their own DB sessions directly (they aren't
    # FastAPI endpoints), so point their module-level SessionLocal at the same
    # test engine rather than the real one.
    monkeypatch.setattr("app.agents.review_graph.SessionLocal", testing_session_local)
    monkeypatch.setattr("app.agents.retest_graph.SessionLocal", testing_session_local)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def fake_github(monkeypatch):
    FakeGitHubClient.pr_to_issue = {}
    FakeGitHubClient.calls = []
    monkeypatch.setattr("app.routers.defects.GitHubClient", FakeGitHubClient)
    monkeypatch.setattr("app.routers.retests.GitHubClient", FakeGitHubClient)
    monkeypatch.setattr("app.agents.review_graph.GitHubClient", FakeGitHubClient)
    monkeypatch.setattr("app.agents.retest_graph.GitHubClient", FakeGitHubClient)
    return FakeGitHubClient


def test_approved_review_merges_and_passing_retest_closes_the_defect(client, monkeypatch):
    # 1. Raise Defect
    resp = client.post("/defects", json={"title": "Blank titles accepted", "slug": "empty_title"})
    assert resp.status_code == 200
    defect = resp.json()
    issue_number = defect["github_issue_number"]
    assert defect["status"] == "open"

    # A human opened a PR whose body says "Fixes #<issue_number>".
    pr_number = 42
    FakeGitHubClient.pr_to_issue[pr_number] = issue_number

    # 2. AI Reviews PR (approves) -> 3. Merge
    monkeypatch.setattr(
        "app.agents.review_graph.ask_json",
        lambda prompt: {"approve": True, "summary": "Fix looks correct.", "comments": []},
    )
    resp = client.post("/reviews/run", json={"pr_number": pr_number}, headers=SERVICE_TOKEN_HEADER)
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "approve"
    assert ("merge_pr", pr_number) in FakeGitHubClient.calls

    # 4. AI Retests (passes) -> 5. Close Defect
    monkeypatch.setattr(
        "app.agents.retest_graph.subprocess.run",
        lambda *a, **k: FakeCompletedProcess(returncode=0, stdout="3 passed"),
    )
    monkeypatch.setattr(
        "app.agents.retest_graph.ask_json",
        lambda prompt: {"passed": True, "summary": "All specs pass; the fix works."},
    )
    resp = client.post("/retests/run", json={"pr_number": pr_number}, headers=SERVICE_TOKEN_HEADER)
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
    assert ("close_issue", issue_number) in FakeGitHubClient.calls

    resp = client.get(f"/defects/{defect['id']}")
    assert resp.json()["status"] == "closed"


def test_failed_retest_reopens_the_defect_instead_of_closing_it(client, monkeypatch):
    resp = client.post("/defects", json={"title": "Wrong delete", "slug": "wrong_delete"})
    defect = resp.json()
    issue_number = defect["github_issue_number"]

    pr_number = 43
    FakeGitHubClient.pr_to_issue[pr_number] = issue_number
    monkeypatch.setattr(
        "app.agents.review_graph.ask_json",
        lambda prompt: {"approve": True, "summary": "ok", "comments": []},
    )
    client.post("/reviews/run", json={"pr_number": pr_number}, headers=SERVICE_TOKEN_HEADER)

    # Playwright actually failed - the LLM's opinion must not override that.
    monkeypatch.setattr(
        "app.agents.retest_graph.subprocess.run",
        lambda *a, **k: FakeCompletedProcess(returncode=1, stdout="1 failed"),
    )
    monkeypatch.setattr(
        "app.agents.retest_graph.ask_json",
        lambda prompt: {"passed": True, "summary": "The model thinks it passed, but pytest disagrees."},
    )
    resp = client.post("/retests/run", json={"pr_number": pr_number}, headers=SERVICE_TOKEN_HEADER)
    assert resp.json()["passed"] is False
    assert ("reopen_issue", issue_number) in FakeGitHubClient.calls

    resp = client.get(f"/defects/{defect['id']}")
    assert resp.json()["status"] == "open"


def test_rejected_review_does_not_merge(client, monkeypatch):
    resp = client.post("/defects", json={"title": "Toggle all", "slug": "toggle_all"})
    defect = resp.json()
    pr_number = 44
    FakeGitHubClient.pr_to_issue[pr_number] = defect["github_issue_number"]

    monkeypatch.setattr(
        "app.agents.review_graph.ask_json",
        lambda prompt: {"approve": False, "summary": "Still toggles every row.", "comments": ["fix the loop"]},
    )
    resp = client.post("/reviews/run", json={"pr_number": pr_number}, headers=SERVICE_TOKEN_HEADER)
    assert resp.json()["verdict"] == "request_changes"
    assert not any(call[0] == "merge_pr" for call in FakeGitHubClient.calls)


def test_reviews_endpoint_rejects_missing_service_token(client):
    resp = client.post("/reviews/run", json={"pr_number": 1})
    assert resp.status_code in (401, 422)
