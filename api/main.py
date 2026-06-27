"""
FastAPI entry point for the Dividend Recovery System backend.
"""
import sys
from pathlib import Path

# Make project modules (database.database, providers, etc.) importable
# regardless of whether the app is run from the repo root or elsewhere.
_project_root = Path(__file__).resolve().parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.stocks import router as stocks_router

app = FastAPI(
    title="Dividend Recovery API",
    version="0.1.0",
    description="Backend API for the Dividend Recovery System.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(stocks_router, prefix="/api/v1")
