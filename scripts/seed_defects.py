from __future__ import annotations

import httpx

API_BASE = "http://127.0.0.1:8000"

SEED_DEFECTS = [
    {
        "slug": "empty_title",
        "title": "Todo app accepts blank/whitespace-only todo titles",
        "description": (
            "Steps to reproduce:\n"
            "1. Open the demo todo app.\n"
            "2. Submit the 'Add' form with an empty or whitespace-only title.\n\n"
            "Expected: the submission is rejected and no todo is created.\n"
            "Actual: a blank todo item is added to the list."
        ),
    },
    {
        "slug": "wrong_delete",
        "title": "Deleting a todo removes the wrong item",
        "description": (
            "Steps to reproduce:\n"
            "1. Add three todos: A, B, C.\n"
            "2. Delete todo B by its id.\n\n"
            "Expected: only B is removed, A and C remain.\n"
            "Actual: the delete endpoint treats the todo id as a list position, "
            "removing whatever item currently sits at that index instead of B."
        ),
    },
    {
        "slug": "toggle_all",
        "title": "Marking one todo complete toggles every todo",
        "description": (
            "Steps to reproduce:\n"
            "1. Add two todos: A, B.\n"
            "2. Click 'Complete' on A only.\n\n"
            "Expected: only A is marked done.\n"
            "Actual: both A and B flip their done state."
        ),
    },
]


def main() -> None:
    for bug in SEED_DEFECTS:
        response = httpx.post(f"{API_BASE}/defects", json=bug, timeout=30)
        response.raise_for_status()
        defect = response.json()
        print(f"Raised defect #{defect['github_issue_number']} ({bug['slug']}): {bug['title']}")


if __name__ == "__main__":
    main()
