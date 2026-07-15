from fastapi import FastAPI, Request
from routes import router as entries_router
import time


async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
    return response


app = FastAPI()

app.middleware("http")(timing_middleware)

app.include_router(entries_router)
