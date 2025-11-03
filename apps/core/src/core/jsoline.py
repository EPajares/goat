"""
Translated from https://github.com/plan4better/goat/blob/0089611acacbebf4e2978c404171ebbae75591e2/app/client/src/utils/Jsolines.js
"""

import math
from typing import Any, Sequence

import numpy as np
from geopandas import GeoDataFrame
from numba import njit
from numpy.typing import NDArray
from shapely.geometry import shape

from core.utils import compute_r5_surface, coordinate_from_pixel, decode_r5_grid

MAX_COORDS = 20000


@njit
def get_contour(surface: NDArray[np.float64], width: int, height: int, cutoff: float) -> NDArray[np.int8]:
    """
    Get a contouring grid. Exported for testing purposes, not generally used
    outside jsolines testing
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
    Follow the loop
    We keep track of which contour cell we're in, and we always keep the filled
    area to our left. Thus we always indicate only which direction we exit the
    cell.
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
    Do linear interpolation
    """
    #   The edges are always considered unreachable to avoid edge effects so set
    #   them to the cutoff.
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


# Calculated fractions may not be numbers causing interpolation to fail.
@njit
def ensure_fraction_is_number(frac: float, direction: str) -> float:
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
                            f"Unexpected coo rdinate shift from ${start[0]}, ${start[1]} to ${pos[0]}, ${pos[1]}, discarding ring"
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
            # Workaroudn (x+y) to avoid float to str type conversion in numba
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
) -> dict[str, Any]:
    """
    Calculate isolines from a surface.

    :param surface: A 2D array of values.
    :param width: The width of the surface.
    :param height: The height of the surface.
    :param west: The western edge of the surface.
    :param north: The northern edge of the surface.
    :param zoom: The zoom level of the surface.
    :param cutoffs: A list of cutoff values.
    :param interpolation: Whether to interpolate between pixels.
    :param return_incremental: Whether to also return incremental isolines. Takes
    :param web_mercator: Whether to use web mercator coordinates.

    :return: A dictionary with full and/or incremental isolines as a geodataframe object.
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
) -> dict[str, Any]:
    """
    Generate the jsolines from the isochrones.

    :return: A GeoDataFrame with the jsolines.

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


if __name__ == "__main__":
    file_name = "/app/src/tests/data/isochrone/public_transport_calculation.bin"
    with open(file_name, mode="rb") as file:  # b is important -> binary
        file_content = file.read()

        grid_decoded = decode_r5_grid(file_content)
        grid_decoded["surface"] = compute_r5_surface(
            grid_decoded,
            5,
        )

        cutoffs = np.arange(60, 61)
        isochrones = jsolines(
            grid_decoded["surface"],
            grid_decoded["width"],
            grid_decoded["height"],
            grid_decoded["west"],
            grid_decoded["north"],
            grid_decoded["zoom"],
            cutoffs,
            return_incremental=True,
            web_mercator=False,
        )
