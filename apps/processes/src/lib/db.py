"""Database utilities for processes app.

Re-exports database models from core to avoid duplication.
Provides async session factory for direct database access.
"""

import sys
from pathlib import Path

# Add core's src directory to path so we can import from it
core_src_path = str(Path(__file__).parent.parent.parent.parent.parent / "core" / "src")
if core_src_path not in sys.path:
    sys.path.insert(0, core_src_path)

# Import env variables from core (needed before importing core modules)
import core._dotenv  # noqa: E402, F401, I001

# Re-export models and enums from core
from core.db.models import Job, Layer  # noqa: E402
from core.db.models._link_model import LayerProjectLink  # noqa: E402
from core.db.models.layer import (  # noqa: E402
    FeatureGeometryType,
    FeatureType,
    FileUploadType,
    LayerType,
)

# Also re-export job-related types
from core.schemas.job import JobStatusType, JobType  # noqa: E402

# =============================================================================
# Session Factory (processes-specific, avoids full core dependency)
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from lib.config import get_settings  # noqa: E402


async def get_async_session():
    """Create an async database session.

    Returns:
        Tuple of (engine, async_session_factory)
    """
    settings = get_settings()
    engine = create_async_engine(
        settings.ASYNC_POSTGRES_DATABASE_URI,
        echo=False,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, async_session


# Export everything that was previously available
__all__ = [
    # Models
    "Job",
    "Layer",
    "LayerProjectLink",
    # Enums
    "FeatureGeometryType",
    "FeatureType",
    "FileUploadType",
    "LayerType",
    "JobStatusType",
    "JobType",
    # Session
    "get_async_session",
]
