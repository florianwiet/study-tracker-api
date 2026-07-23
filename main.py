from fastapi import FastAPI, Request
from routes import router as entries_router
import time
from contextlib import asynccontextmanager

from db import create_db_and_tables


async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
    return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.middleware("http")(timing_middleware)

app.include_router(entries_router)


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok"}
