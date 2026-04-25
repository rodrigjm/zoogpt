"""Admin API routers."""

from .analytics import router as analytics_router
from .kb import router as kb_router
from .config import router as config_router
from .images import router as images_router
from .feedback import router as feedback_router
from .pipeline import router as pipeline_router

__all__ = ["analytics_router", "kb_router", "config_router", "images_router", "feedback_router", "pipeline_router"]
