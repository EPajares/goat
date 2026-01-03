"""
Catchment Area Analysis - Isochrone/Isoline Generation.

This module provides:
1. CatchmentAreaTool - A tool for computing catchment areas from R5 or routing responses
2. CatchmentAreaService - HTTP client for calling R5 and GOAT routing services
3. Functions to decode binary grid data from R5 routing engine
4. Functions to generate isolines (isochrones) from travel time grid data using marching squares

Original isoline implementation from:
https://github.com/plan4better/goat/blob/0089611acacbebf4e2978c404171ebbae75591e2/app/client/src/utils/Jsolines.js
"""

import asyncio
import json
import logging
import math
from pathlib import Path
from typing import Any, Self, Sequence

import numpy as np
from geopandas import GeoDataFrame
from numba import njit
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from shapely.geometry import shape

from goatlib.analysis.core.base import AnalysisTool
from goatlib.config.settings import settings

logger = logging.getLogger(__name__)

MAX_COORDS = 20000


# =============================================================================
# R5 Grid Decoding
# =============================================================================


def decode_r5_grid(grid_data_buffer: bytes) -> dict[str, Any]:
    """
    Decode R5 grid data from binary format.

    The R5 grid format consists of:
    - 8-byte header type (should be "ACCESSGR")
    - 7 int32 header entries: version, zoom, west, north, width, height, depth
    - Grid data: width * height * depth int32 values (delta-encoded)
    - JSON metadata at the end

    Args:
        grid_data_buffer: Raw binary data from R5 response

    Returns:
        Dictionary containing:
        - header fields (zoom, west, north, width, height, depth, version)
        - data: numpy array of travel times
        - metadata fields from JSON

    Raises:
        ValueError: If grid type or version is invalid
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
        raise ValueError(
            f"Invalid grid type: {header_type}, expected {times_grid_type}"
        )
    ## - get header data
    header_raw = np.frombuffer(
        grid_data_buffer, count=header_entries, offset=8, dtype=np.int32
    )
    version = header_raw[0]
    if version != current_version:
        raise ValueError(f"Invalid grid version: {version}, expected {current_version}")
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

    return dict(header | metadata | {"data": data, "errors": [], "warnings": []})


# =============================================================================
# Coordinate Conversion
# =============================================================================


@njit(cache=True)
def z_scale(z: int) -> int:
    """
    Convert zoom level to pixel scale.

    2^z represents the tile number. Scale that by the number of pixels in each tile.
    """
    pixels_per_tile = 256
    return int(2**z * pixels_per_tile)


@njit(cache=True)
def pixel_to_longitude(pixel_x: float, zoom: int) -> float:
    """Convert pixel x coordinate to longitude."""
    return float((pixel_x / z_scale(zoom)) * 360 - 180)


@njit(cache=True)
def pixel_to_latitude(pixel_y: float, zoom: int) -> float:
    """Convert pixel y coordinate to latitude."""
    lat_rad = math.atan(math.sinh(math.pi * (1 - (2 * pixel_y) / z_scale(zoom))))
    return lat_rad * 180 / math.pi


@njit(cache=True)
def pixel_x_to_web_mercator_x(x: float, zoom: int) -> float:
    """Convert pixel x to Web Mercator x."""
    return float(x * (40075016.68557849 / (z_scale(zoom))) - (40075016.68557849 / 2.0))


@njit(cache=True)
def pixel_y_to_web_mercator_y(y: float, zoom: int) -> float:
    """Convert pixel y to Web Mercator y."""
    return float(
        y * (40075016.68557849 / (-1 * z_scale(zoom))) + (40075016.68557849 / 2.0)
    )


@njit(cache=True)
def coordinate_from_pixel(
    input: list[float], zoom: int, round_int: bool = False, web_mercator: bool = False
) -> list[float]:
    """
    Convert pixel coordinate to longitude and latitude.

    Args:
        input: [x, y] pixel coordinates
        zoom: Zoom level
        round_int: Whether to round to integers
        web_mercator: Whether to output in Web Mercator (EPSG:3857)

    Returns:
        [x, y] in geographic or Web Mercator coordinates
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


# =============================================================================
# Surface Computation
# =============================================================================


def compute_r5_surface(
    grid: dict[str, Any], percentile: int
) -> NDArray[np.uint16] | None:
    """
    Compute single value surface from the grid.

    Args:
        grid: Decoded R5 grid data
        percentile: Percentile to extract (5, 25, 50, 75, 95)

    Returns:
        1D numpy array of travel times for the requested percentile
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
        surface: NDArray[Any] = grid["data"]
    else:
        grid_percentiles = np.reshape(grid["data"], (grid["depth"], -1))
        surface = grid_percentiles[percentile_index]

    return surface.astype(np.uint16)


# =============================================================================
# Marching Squares Contouring
# =============================================================================


@njit
def get_contour(
    surface: NDArray[np.float64], width: int, height: int, cutoff: float
) -> NDArray[np.int8]:
    """
    Get a contouring grid using marching squares lookup.

    Creates a grid where each cell is assigned an index (0-15) based on which
    corners are inside the isochrone (below the cutoff value).
    """
    contour = np.zeros((width - 1) * (height - 1), dtype=np.int8)

    # compute contour values for each cell
    for x in range(width - 1):
        for y in range(height - 1):
            index = y * width + x
            top_left = surface[index] < cutoff
            top_right = surface[index + 1] < cutoff
            bot_left = surface[index + width] < cutoff
            bot_right = surface[index + width + 1] < cutoff

            # if we're at the edge of the area, set the outer sides to false, so that
            # isochrones always close even when they actually extend beyond the edges
            # of the surface

            if x == 0:
                top_left = bot_left = False
            if x == width - 2:
                top_right = bot_right = False
            if y == 0:
                top_left = top_right = False
            if y == height - 2:
                bot_right = bot_left = False

            idx = 0

            if top_left:
                idx |= 1 << 3
            if top_right:
                idx |= 1 << 2
            if bot_right:
                idx |= 1 << 1
            if bot_left:
                idx |= 1

            contour[y * (width - 1) + x] = idx

    return contour


@njit
def follow_loop(idx: int, xy: Sequence[int], prev_xy: Sequence[int]) -> list[int]:
    """
    Follow the loop using marching squares lookup.

    We keep track of which contour cell we're in, and we always keep the filled
    area to our left. Thus we always indicate only which direction we exit the cell.
    """
    x = xy[0]
    y = xy[1]
    prevx = prev_xy[0]
    prevy = prev_xy[1]

    if idx in (1, 3, 7):
        return [x - 1, y]
    elif idx in (2, 6, 14):
        return [x, y + 1]
    elif idx in (4, 12, 13):
        return [x + 1, y]
    elif idx == 5:
        # Assume that saddle has // orientation (as opposed to \\). It doesn't
        # really matter if we're wrong, we'll just have two disjoint pieces
        # where we should have one, or vice versa.
        # From Bottom:
        if prevy > y:
            return [x + 1, y]

        # From Top:
        if prevy < y:
            return [x - 1, y]

        return [x, y]
    elif idx in (8, 9, 11):
        return [x, y - 1]
    elif idx == 10:
        # From left
        if prevx < x:
            return [x, y + 1]

        # From right
        if prevx > x:
            return [x, y - 1]

        return [x, y]

    else:
        return [x, y]


@njit
def interpolate(
    pos: Sequence[int],
    cutoff: float,
    start: Sequence[int],
    surface: NDArray[np.float64],
    width: int,
    height: int,
) -> list[float] | None:
    """
    Do linear interpolation to find exact position on cell edge.
    """
    x = pos[0]
    y = pos[1]
    startx = start[0]
    starty = start[1]
    index = y * width + x
    top_left = surface[index]
    top_right = surface[index + 1]
    bot_left = surface[index + width]
    bot_right = surface[index + width + 1]
    if x == 0:
        top_left = bot_left = cutoff
    if y == 0:
        top_left = top_right = cutoff
    if y == height - 2:
        bot_right = bot_left = cutoff
    if x == width - 2:
        top_right = bot_right = cutoff
    # From left
    if startx < x:
        frac = (cutoff - top_left) / (bot_left - top_left)
        return [x, y + ensure_fraction_is_number(frac, "left")]
    # From right
    if startx > x:
        frac = (cutoff - top_right) / (bot_right - top_right)
        return [x + 1, y + ensure_fraction_is_number(frac, "right")]
    # From bottom
    if starty > y:
        frac = (cutoff - bot_left) / (bot_right - bot_left)
        return [x + ensure_fraction_is_number(frac, "bottom"), y + 1]
    # From top
    if starty < y:
        frac = (cutoff - top_left) / (top_right - top_left)
        return [x + ensure_fraction_is_number(frac, "top"), y]
    return None


@njit
def no_interpolate(pos: Sequence[int], start: Sequence[int]) -> list[float] | None:
    """Get midpoint coordinates without interpolation."""
    x = pos[0]
    y = pos[1]
    startx = start[0]
    starty = start[1]
    # From left
    if startx < x:
        return [x, y + 0.5]
    # From right
    if startx > x:
        return [x + 1, y + 0.5]
    # From bottom
    if starty > y:
        return [x + 0.5, y + 1]
    # From top
    if starty < y:
        return [x + 0.5, y]
    return None


@njit
def ensure_fraction_is_number(frac: float, direction: str) -> float:
    """Ensure calculated fractions are valid numbers."""
    if math.isnan(frac) or math.isinf(frac):
        return 0.5
    return frac


@njit
def calculate_jsolines(
    surface: NDArray[np.float64],
    width: int,
    height: int,
    west: float,
    north: float,
    zoom: int,
    cutoffs: NDArray[np.float64],
    interpolation: bool = True,
    web_mercator: bool = True,
) -> list[list[Any]]:
    """
    Calculate isoline geometries from a surface.

    Uses marching squares algorithm to trace contour lines around areas
    that are below each cutoff value.
    """
    geometries = []
    for _, cutoff in np.ndenumerate(cutoffs):
        contour = get_contour(surface, width, height, cutoff)
        c_width = width - 1
        # Store warnings
        warnings = []

        # JavaScript does not have boolean arrays.
        found = np.zeros((width - 1) * (height - 1), dtype=np.int8)

        # DEBUG, comment out to save memory
        indices = []

        # We'll sort out what shell goes with what hole in a bit.
        shells = []
        holes = []

        # Find a cell that has a line in it, then follow that line, keeping filled
        # area to your left. This lets us use winding direction to determine holes.

        for origy in range(height - 1):
            for origx in range(width - 1):
                index = origy * c_width + origx
                if found[index] == 1:
                    continue
                idx = contour[index]

                # Continue if there is no line here or if it's a saddle, as we don't know which way the saddle goes.
                if idx == 0 or idx == 5 or idx == 10 or idx == 15:
                    continue

                # Huzzah! We have found a line, now follow it, keeping the filled area to our left,
                # which allows us to use the winding direction to determine what should be a shell and
                # what should be a hole
                pos = [origx, origy]
                prev = [-1, -1]
                start = [-1, -1]

                # Track winding direction
                direction = 0
                coords = []

                # Make sure we're not traveling in circles.
                # NB using index from _previous_ cell, we have not yet set an index for this cell

                while found[index] != 1:
                    prev = start
                    start = pos
                    idx = contour[index]

                    indices.append(idx)

                    # Mark as found if it's not a saddle because we expect to reach saddles twice.
                    if idx != 5 and idx != 10:
                        found[index] = 1

                    if idx == 0 or idx >= 15:
                        warnings.append("Ran off outside of ring")
                        break

                    # Follow the loop
                    pos = follow_loop(idx, pos, prev)
                    index = pos[1] * c_width + pos[0]

                    # Keep track of winding direction
                    direction += (pos[0] - start[0]) * (pos[1] + start[1])

                    # Shift exact coordinates
                    if interpolation:
                        coord = interpolate(pos, cutoff, start, surface, width, height)
                    else:
                        coord = no_interpolate(pos, start)

                    if not coord:
                        warnings.append(
                            f"Unexpected coordinate shift from ${start[0]}, ${start[1]} to ${pos[0]}, ${pos[1]}, discarding ring"
                        )
                        break
                    xy = coordinate_from_pixel(
                        [coord[0] + west, coord[1] + north],
                        zoom=zoom,
                        web_mercator=web_mercator,
                    )
                    coords.append(xy)

                    # We're back at the start of the ring
                    if pos[0] == origx and pos[1] == origy:
                        coords.append(coords[0])  # close the ring

                        # make it a fully-fledged GeoJSON object
                        geom = [coords]

                        # Check winding direction. Positive here means counter clockwise,
                        # see http:#stackoverflow.com/questions/1165647
                        # +y is down so the signs are reversed from what would be expected
                        if direction > 0:
                            shells.append(geom)
                        else:
                            holes.append(geom)
                        break

        # Shell game time. Sort out shells and holes.
        for hole in holes:
            # Only accept holes that are at least 2-dimensional.
            # Workaround (x+y) to avoid float to str type conversion in numba
            vertices = []
            for x, y in hole[0]:
                vertices.append((x + y))

            if len(vertices) >= 3:
                # NB this is checking whether the first coordinate of the hole is inside
                # the shell. This is sufficient as shells don't overlap, and holes are
                # guaranteed to be completely contained by a single shell.
                hole_point = hole[0][0]
                containing_shell = []
                for shell in shells:
                    if pointinpolygon(hole_point[0], hole_point[1], shell[0]):
                        containing_shell.append(shell)
                if len(containing_shell) == 1:
                    containing_shell[0].append(hole[0])

        geometries.append(list(shells))
    return geometries


@njit
def pointinpolygon(x: float, y: float, poly: NDArray[np.float64]) -> bool:
    """Check if point is inside polygon using ray casting."""
    n = len(poly)
    inside = False
    p2x = 0.0
    p2y = 0.0
    xints = 0.0
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


# =============================================================================
# High-Level API
# =============================================================================


def jsolines(
    surface: NDArray[np.uint16],
    width: int,
    height: int,
    west: float,
    north: float,
    zoom: int,
    cutoffs: NDArray[np.float16 | np.int16],
    interpolation: bool = True,
    return_incremental: bool = False,
    web_mercator: bool = False,
) -> dict[str, GeoDataFrame]:
    """
    Calculate isolines from a surface.

    Args:
        surface: 1D array of travel time values
        width: Width of the grid
        height: Height of the grid
        west: Western edge pixel coordinate
        north: Northern edge pixel coordinate
        zoom: Zoom level
        cutoffs: Array of cutoff values (travel times in minutes)
        interpolation: Whether to interpolate between pixels
        return_incremental: Whether to also return incremental isolines
        web_mercator: Whether to use Web Mercator coordinates (EPSG:3857)

    Returns:
        Dictionary with:
        - 'full': GeoDataFrame with cumulative isolines
        - 'incremental': GeoDataFrame with difference isolines (if return_incremental=True)
    """
    isochrone_multipolygon_coordinates = calculate_jsolines(
        surface, width, height, west, north, zoom, cutoffs, interpolation, web_mercator
    )

    result = {}
    isochrone_shapes = []
    for isochrone in isochrone_multipolygon_coordinates:
        isochrone_shapes.append(
            shape({"type": "MultiPolygon", "coordinates": isochrone})
        )

    result["full"] = GeoDataFrame({"geometry": isochrone_shapes, "minute": cutoffs})

    if return_incremental:
        isochrone_diff = []
        for i in range(len(isochrone_shapes)):
            if i == 0:
                isochrone_diff.append(isochrone_shapes[i])
            else:
                isochrone_diff.append(
                    isochrone_shapes[i].difference(isochrone_shapes[i - 1])
                )

        result["incremental"] = GeoDataFrame(
            {"geometry": isochrone_diff, "minute": cutoffs}
        )

    crs = "EPSG:4326"
    if web_mercator:
        crs = "EPSG:3857"
    for key in result:
        result[key].crs = crs

    return result


def generate_jsolines(
    grid: dict[str, Any],
    travel_time: int,
    percentile: int,
    steps: int,
) -> dict[str, GeoDataFrame]:
    """
    Generate isolines from decoded R5 grid data.

    This is the main high-level function that converts R5 response data
    to polygon geometries.

    Args:
        grid: Decoded R5 grid data (from decode_r5_grid)
        travel_time: Maximum travel time in minutes
        percentile: Percentile to use (5, 25, 50, 75, 95)
        steps: Number of isochrone steps

    Returns:
        Dictionary with 'full' and 'incremental' GeoDataFrames
    """
    single_value_surface = compute_r5_surface(
        grid,
        percentile,
    )
    grid["surface"] = single_value_surface
    isochrones = jsolines(
        grid["surface"],
        grid["width"],
        grid["height"],
        grid["west"],
        grid["north"],
        grid["zoom"],
        cutoffs=np.arange(
            start=(travel_time / steps),
            stop=travel_time + 1,
            step=(travel_time / steps),
        ),
        return_incremental=True,
    )
    return isochrones


# =============================================================================
# Catchment Area Tool
# =============================================================================


class CatchmentAreaParams(BaseModel):
    """Parameters for catchment area analysis."""

    r5_binary_path: str | None = Field(
        default=None,
        description="Path to R5 binary response file (.bin)",
    )
    walking_parquet_path: str | None = Field(
        default=None,
        description="Path to walking catchment parquet file from GOAT routing",
    )
    travel_time: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Maximum travel time in minutes",
    )
    steps: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Number of isochrone steps",
    )
    percentile: int = Field(
        default=5,
        description="Percentile to use for R5 data (5, 25, 50, 75, 95)",
    )
    polygon_difference: bool = Field(
        default=True,
        description="Whether to compute difference between time steps",
    )
    output_path: str = Field(
        ...,
        description="Output path for results (parquet or geojson)",
    )


class CatchmentAreaTool(AnalysisTool):
    """
    Tool for computing catchment areas from routing responses.

    Supports:
    - R5 binary responses (public transport)
    - GOAT Routing parquet responses (walking, cycling, car)

    Example usage:
        tool = CatchmentAreaTool()
        result = tool.run(CatchmentAreaParams(
            r5_binary_path="path/to/r5_response.bin",
            travel_time=30,
            steps=6,
            output_path="output/catchment.parquet"
        ))
    """

    def _run_implementation(self: Self, params: CatchmentAreaParams) -> Path:
        """Execute catchment area analysis."""
        logger.info("Starting Catchment Area Analysis")

        if params.r5_binary_path:
            return self._process_r5_response(params)
        elif params.walking_parquet_path:
            return self._process_walking_parquet(params)
        else:
            raise ValueError(
                "Either r5_binary_path or walking_parquet_path must be provided"
            )

    def _process_r5_response(self: Self, params: CatchmentAreaParams) -> Path:
        """Process R5 binary response and generate isochrones."""
        logger.info("Processing R5 binary response: %s", params.r5_binary_path)

        # Load R5 binary data
        with open(params.r5_binary_path, "rb") as f:
            r5_data = f.read()

        # Decode the grid
        grid = decode_r5_grid(r5_data)
        logger.info(
            "Decoded R5 grid: %dx%d, depth=%d",
            grid["width"],
            grid["height"],
            grid["depth"],
        )

        # Generate isochrones
        isochrones = generate_jsolines(
            grid=grid,
            travel_time=params.travel_time,
            percentile=params.percentile,
            steps=params.steps,
        )

        # Select full or incremental based on polygon_difference
        result_key = "incremental" if params.polygon_difference else "full"
        result_gdf = isochrones[result_key]

        # Add cost_step column for compatibility
        result_gdf["cost_step"] = result_gdf["minute"].astype(int)

        # Convert geometry to WKT for parquet storage
        result_gdf["geometry"] = result_gdf["geometry"].apply(lambda g: g.wkt)

        # Export
        output_path = Path(params.output_path)
        if output_path.suffix == ".parquet":
            result_gdf.to_parquet(output_path, index=False)
        else:
            # GeoJSON export
            result_gdf.to_file(output_path, driver="GeoJSON")

        logger.info("Saved catchment area to: %s", output_path)
        return output_path

    def _process_walking_parquet(self: Self, params: CatchmentAreaParams) -> Path:
        """Process walking/cycling parquet from GOAT Routing."""
        import polars as pl

        logger.info(
            "Processing walking parquet response: %s", params.walking_parquet_path
        )

        # Load parquet
        df = pl.read_parquet(params.walking_parquet_path)

        # Filter out empty geometries and step 0 if present
        if "cost_step" in df.columns:
            df = df.filter(pl.col("cost_step") > 0)

        # Ensure output directory exists
        output_path = Path(params.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        if output_path.suffix == ".parquet":
            df.write_parquet(output_path)
        else:
            # Convert to GeoDataFrame for GeoJSON
            gdf = GeoDataFrame(
                df.to_pandas(),
                geometry=GeoDataFrame.from_wkt(
                    df["geometry"].to_pandas(), crs="EPSG:4326"
                ).geometry,
            )
            gdf.to_file(output_path, driver="GeoJSON")

        logger.info("Saved catchment area to: %s", output_path)
        return output_path

    def process_r5_binary(
        self: Self,
        r5_data: bytes,
        travel_time: int = 30,
        percentile: int = 5,
        steps: int = 6,
        polygon_difference: bool = True,
    ) -> GeoDataFrame:
        """
        Process R5 binary response directly and return GeoDataFrame.

        This is a convenience method for processing R5 data without file I/O.

        Args:
            r5_data: Raw binary response from R5
            travel_time: Maximum travel time in minutes
            percentile: Percentile to use (5, 25, 50, 75, 95)
            steps: Number of isochrone steps
            polygon_difference: Whether to return incremental (True) or full (False) polygons

        Returns:
            GeoDataFrame with catchment area polygons
        """
        grid = decode_r5_grid(r5_data)
        isochrones = generate_jsolines(
            grid=grid,
            travel_time=travel_time,
            percentile=percentile,
            steps=steps,
        )
        result_key = "incremental" if polygon_difference else "full"
        result_gdf = isochrones[result_key]
        result_gdf["cost_step"] = result_gdf["minute"].astype(int)
        return result_gdf


# =============================================================================
# Catchment Area Service - HTTP Client for Routing Services
# =============================================================================


class CatchmentAreaService:
    """
    HTTP client for calling catchment area routing services.

    Supports:
    - GOAT Routing (active mobility: walk, bicycle, pedelec, wheelchair; car)
    - R5 (public transport)

    Configuration is loaded from environment variables via goatlib.config.settings:
    - GOAT_ROUTING_URL: URL for GOAT routing service
    - R5_URL: URL for R5 service
    - ROUTING_AUTHORIZATION: Auth header for routing services (shared)

    Example usage:
        service = CatchmentAreaService()

        # Active mobility catchment
        result = await service.compute_active_mobility_catchment(
            lat=51.7167,
            lon=14.3837,
            routing_type="walking",
            max_traveltime=15,
            speed=5,
            scenario_id="my-scenario",
        )

        # PT catchment
        result = await service.compute_pt_catchment(
            lat=51.7167,
            lon=14.3837,
            max_traveltime=30,
            transit_modes=["bus", "tram"],
            r5_region_id="...",
            r5_bundle_id="...",
        )
    """

    def __init__(
        self: Self,
        goat_routing_url: str | None = None,
        r5_url: str | None = None,
        routing_authorization: str | None = None,
    ) -> None:
        """
        Initialize the service with optional URL overrides.

        If not provided, values are loaded from goatlib.config.settings.routing.
        """
        self.goat_routing_url = goat_routing_url or settings.routing.goat_routing_url
        self.r5_url = r5_url or settings.routing.r5_url
        self.routing_authorization = (
            routing_authorization or settings.routing.routing_authorization
        )
        self.timeout = settings.routing.request_timeout
        self.retries = settings.routing.request_retries
        self.retry_interval = settings.routing.request_retry_interval

    async def compute_active_mobility_catchment(
        self: Self,
        lat: float | list[float],
        lon: float | list[float],
        routing_type: str = "walking",
        max_traveltime: int = 15,
        steps: int = 3,
        speed: float = 5.0,
        catchment_area_type: str = "polygon",
        polygon_difference: bool = True,
        output_format: str = "parquet",
        scenario_id: str | None = None,
    ) -> bytes:
        """
        Compute catchment area for active mobility modes via GOAT Routing.

        Args:
            lat: Latitude(s) of starting point(s) - single value or list
            lon: Longitude(s) of starting point(s) - single value or list
            routing_type: "walking", "bicycle", "pedelec", or "wheelchair"
            max_traveltime: Maximum travel time in minutes
            steps: Number of isochrone steps
            speed: Travel speed in km/h
            catchment_area_type: "polygon", "network", or "rectangular_grid"
            polygon_difference: Whether to compute difference between steps
            output_format: "parquet" or "geojson"
            scenario_id: Optional scenario ID for network modifications

        Returns:
            Raw response bytes (parquet or geojson)
        """
        import httpx

        url = f"{self.goat_routing_url}/active-mobility/catchment-area"

        # Normalize to lists
        lat_list = [lat] if isinstance(lat, (int, float)) else list(lat)
        lon_list = [lon] if isinstance(lon, (int, float)) else list(lon)

        payload = {
            "starting_points": {
                "latitude": lat_list,
                "longitude": lon_list,
            },
            "routing_type": routing_type,
            "travel_cost": {
                "max_traveltime": max_traveltime,
                "steps": steps,
                "speed": speed,
            },
            # Map h3_grid alias to rectangular_grid for the API
            "catchment_area_type": "rectangular_grid"
            if catchment_area_type == "h3_grid"
            else catchment_area_type,
            "output_format": output_format,
        }

        # polygon_difference only applies to polygon type
        if catchment_area_type == "polygon":
            payload["polygon_difference"] = polygon_difference

        if scenario_id:
            payload["scenario_id"] = scenario_id

        headers = {}
        if self.routing_authorization:
            headers["Authorization"] = self.routing_authorization

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(self.retries):
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 202:
                    # Still processing, retry
                    if i == self.retries - 1:
                        raise RuntimeError(
                            "GOAT routing endpoint took too long to process request."
                        )
                    await asyncio.sleep(self.retry_interval)
                    continue
                elif response.status_code in (200, 201):
                    return response.content
                else:
                    raise RuntimeError(
                        f"GOAT routing error ({response.status_code}): {response.text}"
                    )

        raise RuntimeError("Failed to compute catchment area")

    async def compute_car_catchment(
        self: Self,
        lat: float | list[float],
        lon: float | list[float],
        max_traveltime: int = 15,
        steps: int = 3,
        catchment_area_type: str = "polygon",
        polygon_difference: bool = True,
        output_format: str = "parquet",
        scenario_id: str | None = None,
    ) -> bytes:
        """
        Compute catchment area for car mode via GOAT Routing.

        Args:
            lat: Latitude(s) of starting point(s) - single value or list
            lon: Longitude(s) of starting point(s) - single value or list
            max_traveltime: Maximum travel time in minutes
            steps: Number of isochrone steps
            catchment_area_type: "polygon", "network", or "rectangular_grid"
            polygon_difference: Whether to compute difference between steps
            output_format: "parquet" or "geojson"
            scenario_id: Optional scenario ID for network modifications

        Returns:
            Raw response bytes (parquet or geojson)
        """
        import httpx

        url = f"{self.goat_routing_url}/motorized-mobility/catchment-area"

        # Normalize to lists
        lat_list = [lat] if isinstance(lat, (int, float)) else list(lat)
        lon_list = [lon] if isinstance(lon, (int, float)) else list(lon)

        payload = {
            "starting_points": {
                "latitude": lat_list,
                "longitude": lon_list,
            },
            "routing_type": "car",
            "travel_cost": {
                "max_traveltime": max_traveltime,
                "steps": steps,
            },
            "catchment_area_type": catchment_area_type,
            "output_format": output_format,
        }

        # polygon_difference only applies to polygon type
        if catchment_area_type == "polygon":
            payload["polygon_difference"] = polygon_difference

        if scenario_id:
            payload["scenario_id"] = scenario_id

        headers = {}
        if self.routing_authorization:
            headers["Authorization"] = self.routing_authorization

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(self.retries):
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 202:
                    if i == self.retries - 1:
                        raise RuntimeError(
                            "GOAT routing endpoint took too long to process request."
                        )
                    await asyncio.sleep(self.retry_interval)
                    continue
                elif response.status_code in (200, 201):
                    return response.content
                else:
                    raise RuntimeError(
                        f"GOAT routing error ({response.status_code}): {response.text}"
                    )

        raise RuntimeError("Failed to compute car catchment area")

    async def compute_pt_catchment(
        self: Self,
        lat: float,
        lon: float,
        r5_region_id: str,
        r5_bundle_id: str,
        max_traveltime: int = 30,
        steps: int = 6,
        percentile: int = 5,
        transit_modes: list[str] | None = None,
        access_mode: str = "WALK",
        egress_mode: str = "WALK",
        walk_speed: float = 5.0,
        bike_speed: float = 15.0,
        max_walk_time: int = 20,
        max_bike_time: int = 20,
        max_rides: int = 4,
        from_time: int = 25200,  # 07:00
        to_time: int = 32400,  # 09:00
        weekday_date: str = "2024-01-15",
        bounds: dict | None = None,
        zoom: int = 9,
    ) -> bytes:
        """
        Compute catchment area for public transport via R5.

        Args:
            lat: Latitude of starting point
            lon: Longitude of starting point
            r5_region_id: R5 region/project ID
            r5_bundle_id: R5 bundle ID
            max_traveltime: Maximum travel time in minutes
            steps: Number of isochrone steps
            percentile: Percentile (5, 25, 50, 75, 95)
            transit_modes: List of transit modes (BUS, TRAM, RAIL, SUBWAY, FERRY, etc.)
            access_mode: Access mode (WALK, BICYCLE, CAR)
            egress_mode: Egress mode (WALK, BICYCLE)
            walk_speed: Walking speed in km/h
            bike_speed: Biking speed in km/h
            max_walk_time: Max walk time in minutes
            max_bike_time: Max bike time in minutes
            max_rides: Maximum number of transfers + 1
            from_time: Start time in seconds from midnight
            to_time: End time in seconds from midnight
            weekday_date: Date for schedule lookup (YYYY-MM-DD)
            bounds: Bounding box {north, south, east, west}
            zoom: Grid zoom level

        Returns:
            Raw R5 binary response (ACCESSGR format)
        """
        import httpx

        if transit_modes is None:
            transit_modes = ["BUS", "TRAM", "RAIL", "SUBWAY"]

        # Default bounds based on starting point if not provided
        if bounds is None:
            bounds = {
                "north": lat + 0.5,
                "south": lat - 0.5,
                "east": lon + 0.5,
                "west": lon - 0.5,
            }

        payload = {
            "accessModes": access_mode,
            "transitModes": ",".join(transit_modes),
            "bikeSpeed": bike_speed,
            "walkSpeed": walk_speed,
            "bikeTrafficStress": 4,
            "date": weekday_date,
            "fromTime": from_time,
            "toTime": to_time,
            "maxTripDurationMinutes": max_traveltime,
            "decayFunction": {
                "type": "logistic",
                "standard_deviation_minutes": 12,
                "width_minutes": 10,
            },
            "destinationPointSetIds": [],
            "bounds": bounds,
            "directModes": access_mode,
            "egressModes": egress_mode,
            "fromLat": lat,
            "fromLon": lon,
            "zoom": zoom,
            "maxBikeTime": max_bike_time,
            "maxRides": max_rides,
            "maxWalkTime": max_walk_time,
            "monteCarloDraws": 200,
            "percentiles": [5, 25, 50, 75, 95],
            "variantIndex": settings.routing.r5_variant_index,
            "workerVersion": settings.routing.r5_worker_version,
            "regionId": r5_region_id,
            "projectId": r5_region_id,
            "bundleId": r5_bundle_id,
        }

        headers = {}
        if self.routing_authorization:
            headers["Authorization"] = self.routing_authorization

        url = f"{self.r5_url}/api/analysis"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(self.retries):
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 202:
                    if i == self.retries - 1:
                        raise RuntimeError(
                            "R5 engine took too long to process request."
                        )
                    await asyncio.sleep(self.retry_interval)
                    continue
                elif response.status_code == 200:
                    return response.content
                else:
                    raise RuntimeError(
                        f"R5 error ({response.status_code}): {response.text}"
                    )

        raise RuntimeError("Failed to compute PT catchment area")

    async def compute_pt_catchment_as_geodataframe(
        self: Self,
        lat: float,
        lon: float,
        r5_region_id: str,
        r5_bundle_id: str,
        max_traveltime: int = 30,
        steps: int = 6,
        percentile: int = 5,
        polygon_difference: bool = True,
        **kwargs: Any,
    ) -> GeoDataFrame:
        """
        Compute PT catchment and return as GeoDataFrame with polygon geometries.

        This is a convenience method that calls compute_pt_catchment and
        processes the binary response into polygon isochrones.

        Returns:
            GeoDataFrame with columns: geometry, minute, cost_step
        """
        r5_binary = await self.compute_pt_catchment(
            lat=lat,
            lon=lon,
            r5_region_id=r5_region_id,
            r5_bundle_id=r5_bundle_id,
            max_traveltime=max_traveltime,
            percentile=percentile,
            **kwargs,
        )

        grid = decode_r5_grid(r5_binary)
        isochrones = generate_jsolines(
            grid=grid,
            travel_time=max_traveltime,
            percentile=percentile,
            steps=steps,
        )

        result_key = "incremental" if polygon_difference else "full"
        result_gdf = isochrones[result_key]
        result_gdf["cost_step"] = result_gdf["minute"].astype(int)
        return result_gdf
