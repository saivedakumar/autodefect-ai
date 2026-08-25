import os

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("DEMO_APP_URL", "http://127.0.0.1:8001")


def test_blank_title_is_rejected(page: Page):
    page.goto(BASE_URL)
    page.fill('[data-testid="new-todo-input"]', "   ")
    page.click('[data-testid="add-todo-button"]')
    expect(page.locator('[data-testid="todo-item"]')).to_have_count(0)
