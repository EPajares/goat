"""Per-kind display-config Pydantic models.

These validate the `display_config` blob stored under
`layer.field_config[<column_name>].display_config`. The blob is purely
presentation metadata — it never affects the canonical stored value.
"""

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Either the literal "auto" or an integer in [0, 10].
Decimals = Union[Literal["auto"], int]


class _BaseDisplayConfig(BaseModel):
    """Base for all display configs — extra keys are forbidden."""

    model_config = ConfigDict(extra="forbid")


class StringDisplayConfig(_BaseDisplayConfig):
    """No display config for plain string columns yet."""


class _NumericFormatConfig(_BaseDisplayConfig):
    """Common formatting toggles for numeric kinds."""

    decimals: Decimals = Field(default="auto")
    thousands_separator: bool = False
    abbreviate: bool = False
    always_show_sign: bool = False

    @field_validator("decimals")
    @classmethod
    def _validate_decimals(cls, value: Any) -> Decimals:
        if value == "auto":
            return "auto"
        if isinstance(value, bool):
            # bool is a subclass of int in Python — reject it explicitly
            raise ValueError("decimals must be 'auto' or an int in [0, 10]")
        if isinstance(value, int) and 0 <= value <= 10:
            return value
        raise ValueError("decimals must be 'auto' or an int in [0, 10]")


class NumberDisplayConfig(_NumericFormatConfig):
    """Plain number columns — no unit."""


class AreaDisplayConfig(_NumericFormatConfig):
    """Area columns — unit options are area-specific."""

    unit: Literal["auto", "mm²", "cm²", "m²", "ha", "km²"] = "auto"


class PerimeterDisplayConfig(_NumericFormatConfig):
    """Perimeter columns — same unit options as length."""

    unit: Literal["auto", "mm", "cm", "m", "km"] = "auto"


class LengthDisplayConfig(_NumericFormatConfig):
    """Length columns — same unit options as perimeter."""

    unit: Literal["auto", "mm", "cm", "m", "km"] = "auto"


class BooleanDisplayConfig(_BaseDisplayConfig):
    """No display config for boolean columns yet."""


class DatetimeDisplayConfig(_BaseDisplayConfig):
    """Datetime columns — IANA ``tz`` (default UTC) + optional display format."""

    tz: str = "UTC"
    format: str | None = None


_DISPLAY_CONFIG_MODELS: dict[str, type[_BaseDisplayConfig]] = {
    "string": StringDisplayConfig,
    "number": NumberDisplayConfig,
    "area": AreaDisplayConfig,
    "perimeter": PerimeterDisplayConfig,
    "length": LengthDisplayConfig,
    "datetime": DatetimeDisplayConfig,
    "boolean": BooleanDisplayConfig,
}


def get_display_config_model(kind: str) -> type[_BaseDisplayConfig] | None:
    """Return the display-config Pydantic model for `kind`, or None."""
    return _DISPLAY_CONFIG_MODELS.get(kind)


def validate_display_config(
    kind: str, raw: dict[str, Any] | None
) -> _BaseDisplayConfig:
    """Validate a raw dict against the kind's display-config model.

    Raises pydantic's ValidationError on bad input; raises ValueError if
    `kind` is unknown.
    """
    model = get_display_config_model(kind)
    if model is None:
        raise ValueError(f"Unknown kind: {kind!r}")
    return model.model_validate(raw or {})
