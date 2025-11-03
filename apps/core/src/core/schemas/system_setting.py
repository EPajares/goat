from uuid import UUID

from pydantic import Field

from core.db.models.system_setting import (
    ClientThemeType,
    LanguageType,
    SystemSettingBase,
    UnitType,
)
from core.utils import optional


class SystemSettingsRead(SystemSettingBase):
    id: UUID
    user_id: UUID


@optional
class SystemSettingsUpdate(SystemSettingBase):
    pass


class SystemSettingsCreate(SystemSettingBase):
    user_id: UUID | None = Field(None, description="System settings owner ID")


default_system_settings = SystemSettingsCreate(
    client_theme=ClientThemeType.dark,
    preferred_language=LanguageType.de,
    unit=UnitType.metric,
)

# Body of request examples
request_examples = {
    "create": {"client_theme": "dark", "preferred_language": "en", "unit": "metric"},
    "update": {
        "client_theme": "light",
        "preferred_language": "de",
        "unit": "imperial",
    },
}
