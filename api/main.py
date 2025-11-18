"""FastAPI backend for code review agents."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from agents.review_agent import ReviewAgent
from agents.fix_agent import FixAgent
from core.config import Settings
from core.logger import get_logger

app = FastAPI(title="Code Review Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)

# Request/Response models
class ReviewRequest(BaseModel):
    pr_id: str
    platform: Optional[str] = None
    llm_provider: Optional[str] = None

class FixRequest(BaseModel):
    pr_id: str
    platform: Optional[str] = None
    llm_provider: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    message: str

class ReviewResponse(BaseModel):
    status: str
    pr_id: str
    pr_title: Optional[str] = None
    files_reviewed: int = 0
    issues_found: int = 0
    comments_posted: int = 0
    tokens_used: Optional[int] = None
    message: Optional[str] = None

class FixResponse(BaseModel):
    status: str
    original_pr_id: str
    fix_pr_id: Optional[str] = None
    fix_pr_url: Optional[str] = None
    fixes_applied: int = 0
    files_modified: int = 0
    message: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Code Review Agent API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/review", response_model=ReviewResponse)
async def review_pr(request: ReviewRequest, background_tasks: BackgroundTasks):
    """
    Run code review on a pull request.

    Args:
        request: Review request with PR ID

    Returns:
        Review results
    """
    try:
        logger.info(f"Received review request for PR {request.pr_id}")

        # Create settings with overrides if provided
        settings_kwargs = {}
        if request.platform:
            settings_kwargs['platform'] = request.platform
        if request.llm_provider:
            settings_kwargs['llm_provider'] = request.llm_provider

        # Create agent
        if settings_kwargs:
            settings = Settings(**settings_kwargs)
            agent = ReviewAgent(settings)
        else:
            agent = ReviewAgent()

        # Run review
        result = agent.run(request.pr_id)

        return ReviewResponse(**result)

    except Exception as e:
        logger.error(f"Review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fix", response_model=FixResponse)
async def fix_pr(request: FixRequest, background_tasks: BackgroundTasks):
    """
    Generate fixes for review comments and create a fix PR.

    Args:
        request: Fix request with PR ID

    Returns:
        Fix results
    """
    try:
        logger.info(f"Received fix request for PR {request.pr_id}")

        # Create settings with overrides if provided
        settings_kwargs = {}
        if request.platform:
            settings_kwargs['platform'] = request.platform
        if request.llm_provider:
            settings_kwargs['llm_provider'] = request.llm_provider

        # Create agent
        if settings_kwargs:
            settings = Settings(**settings_kwargs)
            agent = FixAgent(settings)
        else:
            agent = FixAgent()

        # Run fix
        result = agent.run(request.pr_id)

        return FixResponse(**result)

    except Exception as e:
        logger.error(f"Fix failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    try:
        from core.config import get_settings
        settings = get_settings()

        return {
            "platform": settings.platform.value,
            "llm_provider": settings.llm_provider.value,
            "review_enabled": settings.review_enabled,
            "fix_enabled": settings.fix_enabled,
            "review_depth": settings.review_depth.value,
            "review_focus": settings.review_focus.value,
        }
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
