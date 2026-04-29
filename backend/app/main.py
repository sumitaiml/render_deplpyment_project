"""
Main FastAPI Application
HRTech Platform - AI-powered resume screening and candidate ranking
"""

import logging
from urllib.parse import urlparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core import settings, DatabaseManager
from app.apis import candidates, jobs, ranking
from app.apis import auth

# Setup logging
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def _mask_database_url(url: str) -> str:
    """Hide password in database URLs for safe logging."""
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked_netloc = parsed.netloc.replace(parsed.password, "*****")
            return parsed._replace(netloc=masked_netloc).geturl()
    except ValueError:
        return url
    return url

# Initialize database lazily during startup so the app can still boot
# and expose health/docs endpoints if the database is temporarily unavailable.
_database_ready = False
_database_mode = "uninitialized"


def _reset_database_manager() -> None:
    """Clear cached engine/session state before re-initializing the database."""
    DatabaseManager._engine = None
    DatabaseManager._session_maker = None


def _verify_database_connection() -> None:
    """Ensure the configured database can actually be reached."""
    engine = DatabaseManager.get_engine()
    connection = engine.connect()
    try:
        connection.close()
    finally:
        if not connection.closed:
            connection.close()


def _initialize_database_with_fallback() -> None:
    """Initialize the configured database, falling back to SQLite if needed."""
    global _database_ready, _database_mode

    try:
        _reset_database_manager()
        DatabaseManager.initialize()
        _verify_database_connection()
        DatabaseManager.create_all_tables()
        _database_ready = True
        _database_mode = "primary"
        logger.info("✅ Database initialized and tables ready")
        return
    except Exception as exc:
        logger.exception(f"Primary database initialization failed: {exc}")

    fallback_url = "sqlite:///./hrtech_db.db"
    logger.warning(f"Falling back to local SQLite database: {fallback_url}")
    settings.DATABASE_URL = fallback_url

    try:
        _reset_database_manager()
        DatabaseManager.initialize()
        DatabaseManager.create_all_tables()
        _database_ready = True
        _database_mode = "fallback-sqlite"
        logger.info("✅ SQLite fallback database initialized and tables ready")
    except Exception as fallback_exc:
        _database_ready = False
        _database_mode = "failed"
        logger.exception(f"SQLite fallback initialization failed: {fallback_exc}")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(candidates.router)
app.include_router(jobs.router)
app.include_router(ranking.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HRTech Platform API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "hrtech-platform",
        "version": settings.API_VERSION
    }


@app.get("/api/health")
async def api_health_check():
    """Alias health endpoint used by frontend/gateway checks."""
    return {
        "status": "ok",
        "service": "hrtech-platform",
        "version": settings.API_VERSION
    }


@app.get("/api/config")
async def get_config():
    """Get system configuration (public, non-sensitive info)"""
    return {
        "api_title": settings.API_TITLE,
        "api_version": settings.API_VERSION,
        "features": {
            "bias_mitigation": settings.APPLY_BIAS_MITIGATION,
            "explainability": True,
            "skill_graph_inference": True
        },
        "database": {
            "ready": _database_ready,
            "mode": _database_mode,
        },
        "ranking_weights": {
            "skill_weight": settings.SKILL_WEIGHT,
            "experience_weight": settings.EXPERIENCE_WEIGHT,
            "seniority_weight": settings.SENIORITY_WEIGHT
        }
    }


@app.get("/api/db-status")
async def db_status():
    """Expose whether the backend database initialization succeeded."""
    return {
        "database_ready": _database_ready,
        "database_mode": _database_mode,
        "database_url": _mask_database_url(settings.DATABASE_URL),
    }


def custom_openapi():
    """Custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://hrtech-platform.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Event handlers
@app.on_event("startup")
async def startup():
    """Startup event"""
    logger.info("🚀 HRTech Platform backend starting...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Database: {_mask_database_url(settings.DATABASE_URL)}")
    logger.info(f"Vector DB: {settings.VECTOR_DB_TYPE}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Max upload size: {settings.MAX_FILE_SIZE / (1024 * 1024):.1f} MB")
    logger.info(f"NLP model: {settings.SPACY_MODEL}")
    logger.info(f"SBERT model: {settings.SBERT_MODEL}")

    _initialize_database_with_fallback()
    if not _database_ready:
        logger.warning("Backend will keep running, but auth and data APIs will return 503 until the database is available.")

    logger.info("✅ Backend ready!")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    logger.info("👋 HRTech Platform backend shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
