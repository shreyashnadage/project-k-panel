"""
Tally Sync Platform — Cloud Backend

FastAPI application for receiving and storing extracted accounting data.
"""

import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from cloudplatform.db.database import init_db
from cloudplatform.api.ingest import router as ingest_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tally Sync Platform",
    description="Cloud backend for Tally data synchronization",
    version="0.2.0",
)

# Initialize database
@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")


# Include routers
app.include_router(ingest_router)


# Health check (root)
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "tally-sync-platform",
        "version": "0.2.0",
        "status": "ok"
    }


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "cloudplatform.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
