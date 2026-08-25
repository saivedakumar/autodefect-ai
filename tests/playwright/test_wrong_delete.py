import os

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("DEMO_APP_URL", "http://127.0.0.1:8001")


def _add(page: Page, title: str) -> None:
    page.fill('[data-testid="new-todo-input"]', title)
    page.click('[data-testid="add-todo-button"]')


def test_deleting_one_todo_leaves_the_others_intact(page: Page):
    page.goto(BASE_URL)
    _add(page, "A")
    _add(page, "B")
    _add(page, "C")

    items = page.locator('[data-testid="todo-item"]')
    middle_id = items.nth(1).get_attribute("data-todo-id")
    page.locator(f'[data-todo-id="{middle_id}"] [data-testid="delete-todo-button"]').click()

    expect(items).to_have_count(2)
    remaining_titles = items.locator('[data-testid="todo-title"]').all_inner_texts()
    assert remaining_titles == ["A", "C"]
