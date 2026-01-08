"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import settings

app = FastAPI(
    title="Blog Backend",
    description="Daily blog post generation service for machine shop website",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Blog Backend API", "environment": settings.environment}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "worker_enabled": settings.worker_enabled,
    }


@app.post("/generate")
async def trigger_generation():
    """
    Manually trigger blog post generation.

    This endpoint will be implemented to call the worker logic
    without waiting for the scheduled daily run.
    """
    return JSONResponse(
        status_code=501,
        content={"message": "Manual generation not yet implemented"},
    )


@app.get("/posts")
async def list_posts():
    """
    List recent blog posts from Supabase.

    Optional endpoint for viewing generated posts.
    """
    return JSONResponse(
        status_code=501,
        content={"message": "Post listing not yet implemented"},
    )
