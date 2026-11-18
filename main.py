import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db import create_db_and_tables
from routes import router as entries_router
from stats import router as stats_router

STATIC_DIR = Path(__file__).parent / "static"


async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Lern-Tracker-API",
    description="Lerneinheiten erfassen und auswerten. Dashboard unter /app/",
    version="1.1.0",
    lifespan=lifespan,
)

app.middleware("http")(timing_middleware)

app.include_router(entries_router)
app.include_router(stats_router)

# Dashboard: statische Dateien, spricht dieselbe API wie jeder andere Client
app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="app")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app/")


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok"}
