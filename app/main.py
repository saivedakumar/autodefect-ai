from fastapi import FastAPI

from .db.database import init_db
from .routers import defects, retests, reviews

app = FastAPI(title="AutoDefect AI")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(defects.router)
app.include_router(reviews.router)
app.include_router(retests.router)


@app.get("/health")
def health():
    return {"status": "ok"}
