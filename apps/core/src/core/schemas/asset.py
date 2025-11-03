from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from core.core.config import settings
from core.db.models.asset import AssetType


class AssetRead(BaseModel):
    id: UUID
    file_name: str
    display_name: str | None
    category: str | None
    mime_type: str
    file_size: int
    asset_type: AssetType
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    # Required for computing the URL but excluded from API response
    s3_key: str = Field(exclude=True)

    model_config = {
        "from_attributes": True  # replaces orm_mode
    }

    @computed_field  # new in Pydantic v2
    @property
    def url(self) -> str:
        return f"{settings.ASSETS_URL}/{self.s3_key}"


class AssetUpdate(BaseModel):
    display_name: str | None = None
    category: str | None = None
