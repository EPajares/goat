import polars as pl

SEGMENT_DATA_SCHEMA = {
    "id": pl.Int64,
    "length_m": pl.Float64,
    "length_3857": pl.Float64,
    "class_": pl.Utf8,
    "impedance_slope": pl.Float64,
    "impedance_slope_reverse": pl.Float64,
    "impedance_surface": pl.Float32,
    "coordinates_3857": pl.Utf8,
    "maxspeed_forward": pl.Int16,
    "maxspeed_backward": pl.Int16,
    "source": pl.Int64,
    "target": pl.Int64,
    "h3_3": pl.Int32,
    "h3_6": pl.Int32,
}

CONNECTOR_DATA_SCHEMA = {
    "id": pl.Int64,
    "h3_3": pl.Int32,
    "h3_6": pl.Int32,
}
