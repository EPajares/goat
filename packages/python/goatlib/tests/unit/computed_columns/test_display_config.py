import pytest
from goatlib.computed_columns.display_config import (
    AreaDisplayConfig,
    DatetimeDisplayConfig,
    LengthDisplayConfig,
    NumberDisplayConfig,
    PerimeterDisplayConfig,
    StringDisplayConfig,
    get_display_config_model,
    validate_display_config,
)
from pydantic import ValidationError


def test_string_display_config_empty() -> None:
    cfg = StringDisplayConfig()
    assert cfg.model_dump() == {}


def test_number_display_config_defaults() -> None:
    cfg = NumberDisplayConfig()
    assert cfg.decimals == "auto"
    assert cfg.thousands_separator is False
    assert cfg.abbreviate is False
    assert cfg.always_show_sign is False


def test_number_display_config_decimals_int() -> None:
    cfg = NumberDisplayConfig(decimals=2)
    assert cfg.decimals == 2


def test_number_display_config_decimals_invalid() -> None:
    with pytest.raises(ValidationError):
        NumberDisplayConfig(decimals=11)
    with pytest.raises(ValidationError):
        NumberDisplayConfig(decimals=-1)
    with pytest.raises(ValidationError):
        NumberDisplayConfig(decimals="three")


def test_area_display_config_defaults() -> None:
    cfg = AreaDisplayConfig()
    assert cfg.unit == "auto"
    assert cfg.decimals == "auto"


def test_area_display_config_valid_units() -> None:
    for unit in ("auto", "mm²", "cm²", "m²", "ha", "km²"):
        cfg = AreaDisplayConfig(unit=unit)
        assert cfg.unit == unit


def test_area_display_config_rejects_length_unit() -> None:
    with pytest.raises(ValidationError):
        AreaDisplayConfig(unit="m")


def test_perimeter_display_config_valid_units() -> None:
    for unit in ("auto", "mm", "cm", "m", "km"):
        cfg = PerimeterDisplayConfig(unit=unit)
        assert cfg.unit == unit


def test_length_display_config_valid_units() -> None:
    for unit in ("auto", "mm", "cm", "m", "km"):
        cfg = LengthDisplayConfig(unit=unit)
        assert cfg.unit == unit


def test_datetime_display_config_defaults() -> None:
    cfg = DatetimeDisplayConfig()
    assert cfg.format is None
    assert cfg.tz == "UTC"


def test_datetime_display_config_accepts_tz() -> None:
    cfg = DatetimeDisplayConfig(tz="Europe/Berlin")
    assert cfg.tz == "Europe/Berlin"


def test_datetime_display_config_accepts_format() -> None:
    cfg = DatetimeDisplayConfig(format="YYYY-MM-DD HH:mm")
    assert cfg.format == "YYYY-MM-DD HH:mm"


def test_datetime_display_config_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        DatetimeDisplayConfig(unit="m")


def test_get_display_config_model_returns_correct_class() -> None:
    assert get_display_config_model("string") is StringDisplayConfig
    assert get_display_config_model("number") is NumberDisplayConfig
    assert get_display_config_model("area") is AreaDisplayConfig
    assert get_display_config_model("perimeter") is PerimeterDisplayConfig
    assert get_display_config_model("length") is LengthDisplayConfig
    assert get_display_config_model("datetime") is DatetimeDisplayConfig
    assert get_display_config_model("date") is None
    assert get_display_config_model("time") is None


def test_get_display_config_model_unknown_kind() -> None:
    assert get_display_config_model("does_not_exist") is None


def test_validate_display_config_round_trip() -> None:
    raw = {"unit": "ha", "decimals": 2, "thousands_separator": True}
    cfg = validate_display_config("area", raw)
    assert isinstance(cfg, AreaDisplayConfig)
    assert cfg.unit == "ha"
    assert cfg.decimals == 2
    assert cfg.thousands_separator is True


def test_validate_display_config_rejects_unit_for_string() -> None:
    with pytest.raises(ValidationError):
        # StringDisplayConfig has no `unit` field; extra keys are forbidden
        validate_display_config("string", {"unit": "m"})
