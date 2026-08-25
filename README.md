# AutoDefect AI

Automates the defect lifecycle:

```
Raise Defect -> Developer Fixes -> Create PR -> AI Reviews PR -> Merge -> AI Retests -> Close Defect
```

- **Raise Defect** / **Close Defect** - GitHub Issues (label `defect`), mirrored into SQLite.
- **AI Reviews PR** / **Merge** - a LangGraph agent reads the PR diff, asks a local
  DeepSeek-Coder model (via Ollama) to review it, posts a real PR review, and
  auto-merges on approval.
- **AI Retests** - a second LangGraph agent runs the Playwright spec tied to the
  defect and asks the model to summarize pass/fail, then closes or reopens the issue.
- **Developer Fixes** / **Create PR** stay manual - this pipeline brackets them.

A small demo app (`demo_app/`, a todo list) ships with 3 seeded bugs so the whole
loop can be exercised end-to-end.

## 1. Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed locally, with the model pulled:
  ```bash
  ollama pull deepseek-coder:6.7b
  ```
- A GitHub repo to point this at, and a [PAT](https://github.com/settings/tokens)
  with `repo` scope.
- A self-hosted GitHub Actions runner registered on that repo, labeled
  `self-hosted, ai-pipeline`:
  *Settings -> Actions -> Runners -> New self-hosted runner* on the target repo,
  then follow GitHub's `config.cmd` / `run.cmd` instructions on this machine. Add
  the `ai-pipeline` label when prompted (or add it afterward from the runner's
  settings). Keep the runner running (`run.cmd`) whenever you want the workflows
  to fire.

## 2. Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and fill in `GITHUB_TOKEN`, `GITHUB_REPO`
(`owner/name`), and a `SERVICE_TOKEN` (any random string - it's the shared secret
between the GitHub Actions workflows and the local API).

Add the same `SERVICE_TOKEN` value as a repo secret named `AUTODEFECT_SERVICE_TOKEN`
(*Settings -> Secrets and variables -> Actions*) so the workflows can authenticate.

## 3. Run the services

In one terminal, the AI pipeline service (keep this running):

```bash
uvicorn app.main:app --port 8000
```

In another terminal, the demo app under test:

```bash
uvicorn demo_app.main:app --port 8001
```

## 4. Walk through the loop

1. **Raise the seeded defects** (creates 3 GitHub issues + SQLite rows):
   ```bash
   python scripts/seed_defects.py
   ```
2. **See a defect fail** - run its Playwright spec, e.g.
   `pytest tests/playwright/test_empty_title.py` should fail against the buggy
   `demo_app/main.py`.
3. **Developer fixes it** - edit `demo_app/main.py` (each bug is marked with a
   `# BUG-n` comment) and commit on a branch.
4. **Create a PR** whose title or body includes `Fixes #<issue-number>` (the
   number printed by `seed_defects.py`).
5. **AI reviews it** - `ai-pr-review.yml` fires on the self-hosted runner, the
   `review_graph` LangGraph agent reviews the diff with DeepSeek-Coder, posts a
   review, and merges automatically if approved.
6. **AI retests it** - `ai-retest.yml` fires on the push to `main`, runs the
   matching Playwright spec, and the `retest_graph` agent closes the GitHub issue
   (and marks the defect `closed` in SQLite) if it passes - or reopens it with the
   failure summary if it doesn't.

## Manual smoke test of each stage

With both services running:

```bash
curl -X POST http://127.0.0.1:8000/defects -H "Content-Type: application/json" \
  -d "{\"title\": \"test\", \"description\": \"test\"}"

curl -X POST http://127.0.0.1:8000/reviews/run -H "Content-Type: application/json" \
  -H "X-Service-Token: <your SERVICE_TOKEN>" -d "{\"pr_number\": 1}"

curl -X POST http://127.0.0.1:8000/retests/run -H "Content-Type: application/json" \
  -H "X-Service-Token: <your SERVICE_TOKEN>" -d "{\"pr_number\": 1}"
```

## Tests

```bash
pytest tests/unit                  # LangGraph node logic, mocked LLM/GitHub
pytest tests/integration           # full Raise->Review->Merge->Retest->Close loop,
                                    # fake GitHub/Ollama, no token/model/runner needed
pytest tests/playwright            # demo app specs (needs demo_app running on :8001)
```

`tests/integration/test_full_loop.py` drives the real FastAPI app and real
LangGraph graphs through the entire lifecycle - including the failure path
(a failing retest reopens the defect instead of closing it) and the
rejected-review path (no merge happens) - using fakes for GitHub and Ollama.
It's the fastest way to confirm the pipeline's own logic is wired correctly
before setting up real credentials and a runner.

## Verifying the framework end-to-end

**Without any external services** (proves the pipeline logic itself is correct):

```bash
pytest tests/unit tests/integration -v
```

All 10 tests should pass. This exercises every stage of the diagram - raise,
review, merge, retest, close - with GitHub and Ollama replaced by fakes.

**With the demo app, but still no GitHub/Ollama** (proves the seeded bugs are
real and the fixes actually work):

```bash
uvicorn demo_app.main:app --port 8001 &
pytest tests/playwright -v   # all 3 should FAIL - the bugs are live
```

Then apply a fix from the `# BUG-n` comments in `demo_app/main.py`, restart the
server, and re-run the matching spec - it should now pass.

**With real GitHub + Ollama + the self-hosted runner** (the full live loop):

1. Complete the setup in section 1-3 above (PAT, runner, `ollama pull`, both
   services running).
2. `python scripts/seed_defects.py` and note the 3 issue numbers it prints.
3. Confirm each issue exists on GitHub (labeled `defect`) and each row exists
   via `curl http://127.0.0.1:8000/defects`.
4. Fix one bug, push a branch, open a PR with `Fixes #<n>` in the body.
5. Watch the runner's terminal (`run.cmd`) - `ai-pr-review.yml` should start
   within a few seconds of opening the PR. Check the PR on GitHub for the
   posted AI review, and confirm it auto-merges on approval.
6. Watch for `ai-retest.yml` to fire on the merge to `main`. Confirm the
   linked GitHub issue closes with the AI's summary comment, and that
   `curl http://127.0.0.1:8000/defects/<id>` shows `"status": "closed"`.
7. As a negative-path check, open a second PR that does *not* actually fix its
   bug - the review agent should request changes (no auto-merge), or the
   retest agent should reopen the issue if it slips through.
