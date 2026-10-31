"""Main FastAPI Application Entrypoint."""

from fastapi import FastAPI

from coach_flow import __version__
from coach_flow.assistant.router import router as assistant_router
from coach_flow.config import settings
from coach_flow.discovery.router import router as discovery_router
from coach_flow.whatsapp.router import router as whatsapp_router

app = FastAPI(
    title="CoachFlow API",
    description="AI-powered WhatsApp Assistant for Personal Trainers",
    version=__version__,
    debug=settings.DEBUG,
)

# Include Routers
app.include_router(whatsapp_router)
app.include_router(discovery_router)
app.include_router(assistant_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify service status."""
    return {
        "status": "ok",
        "service": "coach-flow",
        "version": __version__,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to CoachFlow API",
        "docs_url": "/docs",
    }
