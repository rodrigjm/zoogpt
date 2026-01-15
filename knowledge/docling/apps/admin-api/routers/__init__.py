"""Admin API routers."""

from .analytics import router as analytics_router
from .kb import router as kb_router
from .config import router as config_router

__all__ = ["analytics_router", "kb_router", "config_router"]
