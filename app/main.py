from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db.database import init_db
from .routers import defects, retests, reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AutoDefect AI", lifespan=lifespan)

app.include_router(defects.router)
app.include_router(reviews.router)
app.include_router(retests.router)


@app.get("/health")
def health():
    return {"status": "ok"}
