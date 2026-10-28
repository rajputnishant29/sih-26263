from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.config import settings
from backend.app.database import engine, Base
import backend.app.models  # Register all models for Base.metadata
from backend.app.routes import (
    auth,
    dashboard,
    institutions,
    programmes,
    enrolments,
    uploads,
    issues,
    verifications,
    certificates,
    reports,
    audit,
    rules,
    health,
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "EDUTrace: APAAR ID-Based Student Data Management, Admission Reconciliation, "
        "Identity Verification, and Regulatory Analytics Platform for Smart India Hackathon 2026."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all feature routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(institutions.router)
app.include_router(programmes.router)
app.include_router(enrolments.router)
app.include_router(uploads.router)
app.include_router(issues.router)
app.include_router(verifications.router)
app.include_router(certificates.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(rules.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Structured application error handler.
    Prevents leaking internal stack traces or database errors in production.
    """
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system administrator."},
    )
