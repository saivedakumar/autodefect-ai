import os

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("DEMO_APP_URL", "http://127.0.0.1:8001")


def _add(page: Page, title: str) -> None:
    page.fill('[data-testid="new-todo-input"]', title)
    page.click('[data-testid="add-todo-button"]')


def test_toggling_one_todo_does_not_affect_others(page: Page):
    page.goto(BASE_URL)
    _add(page, "A")
    _add(page, "B")

    items = page.locator('[data-testid="todo-item"]')
    first_id = items.nth(0).get_attribute("data-todo-id")
    page.locator(f'[data-todo-id="{first_id}"] [data-testid="toggle-todo-button"]').click()

    titles = page.locator('[data-testid="todo-title"]')
    expect(titles.nth(0)).to_have_css("text-decoration-line", "line-through")
    expect(titles.nth(1)).not_to_have_css("text-decoration-line", "line-through")
