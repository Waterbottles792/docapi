"""FastAPI app. Boots with zero config; OpenAPI docs at /docs."""
from __future__ import annotations

from fastapi import FastAPI

from .api.extract import router as extract_router

app = FastAPI(title="docapi", version="0.1.0")
app.include_router(extract_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
