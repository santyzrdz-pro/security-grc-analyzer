"""ControlMap AI - FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

import app.models  # noqa: F401  (register all ORM models with Base.metadata)
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("controlmap")

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """Apply baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'"
        )
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.SEED_ON_STARTUP:
        from app.seed.seeder import run_seed

        db = SessionLocal()
        try:
            run_seed(db, with_demo=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Seeding failed: %s", exc)
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Automated cybersecurity compliance, risk management, and control-mapping "
        "platform. Maps technical findings to NIST 800-53 controls, scores risk, "
        "tracks remediation, and generates audit-ready reports."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecureHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": settings.PROJECT_NAME,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
