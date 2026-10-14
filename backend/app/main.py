"""FastAPI application entry point for PJ-SELLING-WEBSITE."""

from contextlib import asynccontextmanager
import os as _os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .services.data_loader import get_data_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load data into memory on startup."""
    get_data_store()
    yield


app = FastAPI(
    title="PJ-SELLING-WEBSITE API",
    description="E-commerce demo with product recommendations and related products",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow frontend to access the API
_allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Allow localhost/127.0.0.1 on any local dev port (3000, 3001, ...)
_local_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

# Add production frontend origin(s) if configured
_vercel_url = _os.environ.get("ALLOWED_ORIGIN")
if _vercel_url:
    _allowed_origins.extend(
        [origin.strip() for origin in _vercel_url.split(",") if origin.strip()]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_local_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
