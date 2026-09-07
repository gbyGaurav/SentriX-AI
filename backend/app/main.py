"""UAMD API — Unified AI Multimodal Fraud Intelligence Framework.

FastAPI application entry point.
"""

import os
# Prevent multi-core thread explosion on Render shared hosts (caps memory to free tier 512MB)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["CV_CPU_MAX_THREADS"] = "1"

import logging
import time
import gc
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.routes import analyze, history, health, monitoring
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.database import init_db

setup_logging()
logger = logging.getLogger(__name__)

APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("Starting SentriX API...")
    logger.info(f"Allowed origins: {settings.allowed_origins_list}")
    logger.info(f"LLM enabled: {settings.ENABLE_LLM}")
    logger.info(f"Audio processing: {settings.ENABLE_AUDIO_PROCESSING}")
    logger.info(f"Video processing: {settings.ENABLE_VIDEO_PROCESSING}")

    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database init during startup deferred or encountered error: {e}. App will proceed.")

    try:
        from rapidocr_onnxruntime import RapidOCR
        RapidOCR(use_cls=False, max_side_len=1024)
        logger.info("RapidOCR initialized successfully.")
    except Exception as e:
        logger.warning(f"RapidOCR warm-up skipped: {e}")

    yield

    logger.info("Shutting down SentriX API.")


app = FastAPI(
    title="SentriX API",
    description="SentriX — Unified Multimodal Fraud Intelligence Framework: "
    "Upload anything suspicious and get an AI-powered risk assessment.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
origins = list(settings.allowed_origins_list)
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://sentrix-ai-ashen.vercel.app",
    "https://sentri-x-ai-ashen.vercel.app",
    "https://sentrix-ai.vercel.app",
    "https://sentri-x.vercel.app",
]
for o in default_origins:
    if o not in origins:
        origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# Include routers
app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(health.router)
app.include_router(monitoring.router)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")
