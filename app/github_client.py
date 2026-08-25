from __future__ import annotations

import re

from github import Auth, Github, GithubException
from github.PullRequest import PullRequest as GhPullRequest

from .config import get_settings


class GitHubClient:
    DEFECT_LABEL = "defect"

    def __init__(self) -> None:
        settings = get_settings()
        gh = Github(auth=Auth.Token(settings.github_token))
        self.repo = gh.get_repo(settings.github_repo)

    def create_defect_issue(self, title: str, body: str) -> int:
        issue = self.repo.create_issue(title=title, body=body, labels=[self.DEFECT_LABEL])
        return issue.number

    def list_defect_issues(self, state: str = "open"):
        label = self.repo.get_label(self.DEFECT_LABEL)
        return list(self.repo.get_issues(state=state, labels=[label]))

    def close_issue(self, number: int, comment: str | None = None) -> None:
        issue = self.repo.get_issue(number)
        if comment:
            issue.create_comment(comment)
        issue.edit(state="closed")

    def reopen_issue(self, number: int, comment: str | None = None) -> None:
        issue = self.repo.get_issue(number)
        if comment:
            issue.create_comment(comment)
        issue.edit(state="open")

    def get_pull_request(self, number: int) -> GhPullRequest:
        return self.repo.get_pull(number)

    def get_pr_diff(self, number: int) -> str:
        pr = self.get_pull_request(number)
        chunks = []
        for f in pr.get_files():
            chunks.append(f"--- {f.filename} (+{f.additions}/-{f.deletions})\n{f.patch or ''}")
        return "\n\n".join(chunks)

    def get_linked_issue_number(self, pr_number: int) -> int | None:
        pr = self.get_pull_request(pr_number)
        text = f"{pr.title}\n{pr.body or ''}"
        match = re.search(r"(?:fixes|closes|resolves)\s+#(\d+)", text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def post_review(self, pr_number: int, body: str, approve: bool) -> None:
        pr = self.get_pull_request(pr_number)
        event = "APPROVE" if approve else "REQUEST_CHANGES"
        try:
            pr.create_review(body=body, event=event)
        except GithubException as exc:
            # GitHub refuses APPROVE/REQUEST_CHANGES from the PR author's own
            # token (e.g. the reviewer bot and PR author share credentials, as
            # in a single-account demo). Fall back to a plain comment so the
            # verdict is still visible; a distinct reviewer identity in
            # production won't hit this branch.
            if exc.status == 422 and "own pull request" in str(exc.data):
                prefix = "**AI review verdict: APPROVE**" if approve else "**AI review verdict: REQUEST CHANGES**"
                pr.create_issue_comment(f"{prefix}\n\n{body}")
            else:
                raise

    def merge_pr(self, pr_number: int) -> None:
        pr = self.get_pull_request(pr_number)
        pr.merge(merge_method="squash")
