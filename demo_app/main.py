from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Demo Todo App")
templates = Jinja2Templates(directory="demo_app/templates")

_todos: list[dict] = []
_next_id = 1


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"todos": _todos})


@app.post("/todos")
def add_todo(title: str = Form(...)):
    global _next_id
    # BUG-1 (defect slug: empty_title): no validation - blank/whitespace-only
    # titles are accepted instead of being rejected.
    _todos.append({"id": _next_id, "title": title, "done": False})
    _next_id += 1
    return RedirectResponse("/", status_code=303)


@app.post("/todos/{todo_id}/toggle")
def toggle_todo(todo_id: int):
    # BUG-3 (defect slug: toggle_all): toggles every todo instead of only the
    # one matching todo_id.
    for todo in _todos:
        todo["done"] = not todo["done"]
    return RedirectResponse("/", status_code=303)


@app.post("/todos/{todo_id}/delete")
def delete_todo(todo_id: int):
    # BUG-2 (defect slug: wrong_delete): treats todo_id as a list position
    # instead of matching todo["id"], so it deletes whatever item currently
    # sits at that index.
    if 0 <= todo_id < len(_todos):
        del _todos[todo_id]
    return RedirectResponse("/", status_code=303)


@app.post("/__reset")
def reset():
    """Test-only helper so Playwright specs always start from a clean list."""
    global _todos, _next_id
    _todos = []
    _next_id = 1
    return {"status": "reset"}
