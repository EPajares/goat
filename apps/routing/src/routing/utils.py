import json
import math
import os
from typing import Annotated, Any, Dict, TypedDict

import numpy as np
import numpy.typing as npt
from numba import njit
from rich import print as print


class PixelCoordinates(TypedDict):
    x: float
    y: float


@njit(cache=True)  # type: ignore
def z_scale(z: int) -> int:
    """
    2^z represents the tile number. Scale that by the number of pixels in each tile.
    """
    _2z: int = 2**z
    pixels_per_tile = 256
    return _2z * pixels_per_tile


def longitude_to_pixel(longitude: float, zoom: int) -> float:
    """
    Convert longitude to pixel x coordinate
    """
    z_s: int = z_scale(zoom)
    return ((longitude + 180) / 360) * z_s


def latitude_to_pixel(latitude: float, zoom: int) -> float:
    lat_rad = (latitude * math.pi) / 180
    z_s: int = z_scale(zoom)
    return (
        (1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2
    ) * z_s


@njit(cache=True)  # type: ignore
def web_mercator_x_to_pixel_x(x: float, zoom: int) -> float:
    z_s: int = z_scale(zoom)
    return (x + (40075016.68557849 / 2.0)) / (40075016.68557849 / (z_s))


@njit(cache=True)  # type: ignore
def web_mercator_y_to_pixel_y(y: float, zoom: int) -> float:
    z_s: int = z_scale(zoom)
    return (y - (40075016.68557849 / 2.0)) / (40075016.68557849 / (-1 * z_s))


def coordinate_to_pixel(
    input: Annotated[list[float], 2],
    zoom: int,
    return_dict: bool = True,
    round_int: bool = False,
    web_mercator: bool = False,
) -> Annotated[list[int | float], 2] | PixelCoordinates:
    """
    Convert coordinate to pixel coordinate
    """
    if web_mercator:
        x = web_mercator_x_to_pixel_x(input[0], zoom)
        y = web_mercator_y_to_pixel_y(input[1], zoom)
    else:
        x = longitude_to_pixel(input[0], zoom)
        y = latitude_to_pixel(input[1], zoom)
    if round_int:
        x = round(x)
        y = round(y)
    if return_dict:
        return {"x": x, "y": y}
    else:
        return [x, y]


def compute_r5_surface(
    grid: Dict[str, npt.NDArray[Any]], percentile: int
) -> npt.NDArray[Any] | None:
    """
    Compute single value surface from the grid
    """
    if (
        grid["data"] is None
        or grid["width"] is None
        or grid["height"] is None
        or grid["depth"] is None
    ):
        return None
    travel_time_percentiles = [5, 25, 50, 75, 95]
    percentile_index = travel_time_percentiles.index(percentile)

    if grid["depth"] == 1:
        # if only one percentile is requested, return the grid as is
        surface = grid["data"]
    else:
        grid_percentiles = np.reshape(grid["data"], (grid["depth"], -1))
        surface = grid_percentiles[percentile_index]

    return surface.astype(np.uint16)


@njit(cache=True)  # type: ignore
def coordinate_from_pixel(
    input: Annotated[list[float], 2],
    zoom: int,
    round_int: bool = False,
    web_mercator: bool = False,
) -> Annotated[list[float], 2]:
    """
    Convert pixel coordinate to longitude and latitude
    """
    if web_mercator:
        x = pixel_x_to_web_mercator_x(input[0], zoom)
        y = pixel_y_to_web_mercator_y(input[1], zoom)
    else:
        x = pixel_to_longitude(input[0], zoom)
        y = pixel_to_latitude(input[1], zoom)
    if round_int:
        x = round(x)
        y = round(y)

    return [x, y]


@njit(cache=True)  # type: ignore
def pixel_x_to_web_mercator_x(x: float, zoom: int) -> float:
    """
    Convert pixel x coordinate to web mercator x coordinate
    """
    z_s: int = z_scale(zoom)
    return x * (40075016.68557849 / (z_s)) - (40075016.68557849 / 2.0)


@njit(cache=True)  # type: ignore
def pixel_y_to_web_mercator_y(y: float, zoom: int) -> float:
    """
    Convert pixel y coordinate to web mercator y coordinate
    """
    z_s: int = z_scale(zoom)
    return y * (40075016.68557849 / (-1 * z_s)) + (40075016.68557849 / 2.0)


@njit(cache=True)  # type: ignore
def pixel_to_longitude(pixel_x: float, zoom: int) -> float:
    """
    Convert pixel x coordinate to longitude
    """
    z_s: int = z_scale(zoom)
    return (pixel_x / z_s) * 360 - 180


@njit(cache=True)  # type: ignore
def pixel_to_latitude(pixel_y: float, zoom: int) -> float:
    """
    Convert pixel y coordinate to latitude
    """
    lat_rad = math.atan(math.sinh(math.pi * (1 - (2 * pixel_y) / z_scale(zoom))))
    return lat_rad * 180 / math.pi


def decode_r5_grid(grid_data_buffer: bytes) -> Any:
    """
    Decode R5 grid data
    """
    current_version = 0
    header_entries = 7
    header_length = 9  # type + entries
    times_grid_type = "ACCESSGR"

    # -- PARSE HEADER
    ## - get header type
    header = {}
    header_data = np.frombuffer(grid_data_buffer, count=8, dtype=np.byte)
    header_type = "".join(map(chr, header_data))
    if header_type != times_grid_type:
        raise ValueError("Invalid grid type")
    ## - get header data
    header_raw = np.frombuffer(
        grid_data_buffer, count=header_entries, offset=8, dtype=np.int32
    )
    version = header_raw[0]
    if version != current_version:
        raise ValueError("Invalid grid version")
    header["zoom"] = header_raw[1]
    header["west"] = header_raw[2]
    header["north"] = header_raw[3]
    header["width"] = header_raw[4]
    header["height"] = header_raw[5]
    header["depth"] = header_raw[6]
    header["version"] = version

    # -- PARSE DATA --
    grid_size = header["width"] * header["height"]
    # - skip the header
    data = np.frombuffer(
        grid_data_buffer,
        offset=header_length * 4,
        count=grid_size * header["depth"],
        dtype=np.int32,
    )
    # - reshape the data
    data = data.reshape(header["depth"], grid_size)
    reshaped_data = np.array([], dtype=np.int32)
    for i in range(header["depth"]):
        reshaped_data = np.append(reshaped_data, data[i].cumsum())
    data = reshaped_data
    # - decode metadata
    raw_metadata = np.frombuffer(
        grid_data_buffer,
        offset=(header_length + header["width"] * header["height"] * header["depth"])
        * 4,
        dtype=np.int8,
    )
    metadata = json.loads(raw_metadata.tobytes())

    return header | metadata | {"data": data, "errors": [], "warnings": []}


def make_dir(dir_path: str) -> None:
    """Creates a new directory if it doesn't already exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def format_value_null_sql(value: str) -> str:
    if value is None:
        return "NULL"
    else:
        return f"'{value}'"

def print_info(message: str) -> None:
    print(f"[bold green]INFO[/bold green]: {message}")


def print_error(message: str) -> None:
    print(f"[bold red]ERROR[/bold red]: {message}")


def print_warning(message: str) -> None:
    print(f"[red magenta]WARNING[/red magenta]: {message}")
