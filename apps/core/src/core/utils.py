# Standard library imports
import asyncio
import inspect
import json
import math
import os
import random
import re
import shutil
import string
import subprocess
import time
import zipfile
from functools import wraps
from typing import Any, AsyncIterator, Callable, TypeVar, cast
from uuid import UUID

import aiohttp

# Third party imports
import numpy as np
from fastapi import UploadFile
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from geojson import loads as geojsonloads
from numba import njit
from numpy.typing import NDArray
from pydantic import BaseModel
from pygeofilter.backends.sql import to_sql_where
from pygeofilter.parsers.cql2_json import parse as cql2_json_parser
from rich import print as print
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.schemas.common import CQLQuery, CQLQueryObject


def optional(*fields: Any) -> Any:
    def dec(_cls: type[BaseModel]) -> type[BaseModel]:
        for field in fields:
            # TODO: Take another look at this
            # _cls.__fields__[field].required = False
            if _cls.model_fields[field].default:
                _cls.model_fields[field].default = None
        return _cls

    if fields and inspect.isclass(fields[0]) and issubclass(fields[0], BaseModel):
        cls = fields[0]
        fields = tuple(cls.model_fields.keys())
        return dec(cls)
    return dec


async def table_exists(db: AsyncSession, schema_name: str, table_name: str) -> bool:
    sql_check_table = (
        select(func.count())
        .where(text("table_name = :table_name AND table_schema = :schema_name"))
        .select_from(text("information_schema.tables"))
    )
    params = {"table_name": table_name, "schema_name": schema_name}
    table_exists = await db.execute(sql_check_table, params)
    result = table_exists.scalar()
    return result is not None and result > 0


def encode_r5_grid(grid_data: Any) -> bytes:
    """
    Encode raster grid data
    """
    grid_type = "ACCESSGR"
    grid_type_binary = str.encode(grid_type)
    array = np.array(
        [
            grid_data["version"],
            grid_data["zoom"],
            grid_data["west"],
            grid_data["north"],
            grid_data["width"],
            grid_data["height"],
            grid_data["depth"],
        ],
        dtype=np.int32,
    )
    header_bin = array.tobytes()
    # - reshape the data
    grid_size = grid_data["width"] * grid_data["height"]
    if len(grid_data["data"]) == 0:
        data = np.array([], dtype=np.int32)
    else:
        data = grid_data["data"].reshape(grid_data["depth"], grid_size)
        reshaped_data = np.array([])
        for i in range(grid_data["depth"]):
            reshaped_data = np.append(reshaped_data, np.diff(data[i], prepend=0))
        data = reshaped_data.astype(np.int32)
    z_diff_bin = data.tobytes()

    # - encode metadata
    metadata = {
        "accessibility": grid_data.get("accessibility", {}),
        "errors": grid_data.get("errors", []),
        "warnings": grid_data.get("warnings", []),
        "pathSummaries": grid_data.get("pathSummaries", []),
        "scenarioApplicationWarnings": grid_data.get("scenarioApplicationWarnings", []),
        "scenarioApplicationInfo": grid_data.get("scenarioApplicationInfo", []),
    }
    metadata_bin = json.dumps(metadata).encode("utf-8")

    binary_output = b"".join([grid_type_binary, header_bin, z_diff_bin, metadata_bin])
    return binary_output


def decode_r5_grid(grid_data_buffer: bytes) -> dict[str, Any]:
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

    return dict(header | metadata | {"data": data, "errors": [], "warnings": []})


def compute_r5_surface(
    grid: dict[str, Any], percentile: int
) -> NDArray[np.uint16] | None:
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
        surface: NDArray[Any] = grid["data"]
    else:
        grid_percentiles = np.reshape(grid["data"], (grid["depth"], -1))
        surface = grid_percentiles[percentile_index]

    return surface.astype(np.uint16)


@njit(cache=True)
def z_scale(z: int) -> int:
    """
    2^z represents the tile number. Scale that by the number of pixels in each tile.
    """
    pixels_per_tile = 256
    return int(2**z * pixels_per_tile)


@njit(cache=True)
def pixel_to_longitude(pixel_x: float, zoom: int) -> float:
    """
    Convert pixel x coordinate to longitude
    """
    return float((pixel_x / z_scale(zoom)) * 360 - 180)


@njit(cache=True)
def pixel_to_latitude(pixel_y: float, zoom: int) -> float:
    """
    Convert pixel y coordinate to latitude
    """
    lat_rad = math.atan(math.sinh(math.pi * (1 - (2 * pixel_y) / z_scale(zoom))))
    return lat_rad * 180 / math.pi


@njit(cache=True)
def pixel_x_to_web_mercator_x(x: float, zoom: int) -> float:
    return float(x * (40075016.68557849 / (z_scale(zoom))) - (40075016.68557849 / 2.0))


@njit(cache=True)
def pixel_y_to_web_mercator_y(y: float, zoom: int) -> float:
    return float(
        y * (40075016.68557849 / (-1 * z_scale(zoom))) + (40075016.68557849 / 2.0)
    )


@njit(cache=True)
def coordinate_from_pixel(
    input: list[float], zoom: int, round_int: bool = False, web_mercator: bool = False
) -> list[float]:
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


def delete_file(file_path: str) -> None:
    """Delete file from disk."""

    if os.path.exists(file_path):
        os.remove(file_path)


def delete_dir(dir_path: str) -> None:
    """Delete file from disk."""

    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


def create_dir(dir_path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def print_hashtags() -> None:
    print(
        "#################################################################################################################"
    )


def print_info(message: str) -> None:
    print(f"[bold green]INFO[/bold green]: {message}")


def print_warning(message: str) -> None:
    print(f"[bold red]WARNING[/bold red]: {message}")


F = TypeVar("F", bound=Callable[..., Any])


def timing(f: F) -> F:
    @wraps(f)
    def wrap(*args: Any, **kw: Any) -> Any:
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        total_time = te - ts
        if total_time > 1:
            total_time = round(total_time, 2)
            total_time_string = f"{total_time} seconds"
        else:
            time_miliseconds = int((total_time) * 1000)
            total_time_string = f"{time_miliseconds} miliseconds"

        print(f"func: {f.__name__} took: {total_time_string}")

        return result

    return cast(F, wrap)


def get_random_string(length: int) -> str:
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def get_layer_columns(
    attribute_mapping: dict[str, Any], base_columns: list[str]
) -> list[str]:
    """Get the columns for the layer table and the original table. Add the base columns geom and layer_id"""

    original_columns = ", ".join(attribute_mapping.keys())
    table_columns = ", ".join(attribute_mapping.values())
    additional_columns = ",".join(base_columns)
    additional_columns = "," + additional_columns
    original_columns += additional_columns
    table_columns += additional_columns
    return [original_columns, table_columns]


def sanitize_error_message(message: str) -> str:
    replacements = {
        settings.POSTGRES_SERVER: "HIDDEN_SERVER",
        settings.POSTGRES_DB: "HIDDEN_DB",
        settings.POSTGRES_USER: "HIDDEN_USER",
        settings.POSTGRES_PASSWORD: "HIDDEN_PASSWORD",
        settings.POSTGRES_PORT: "HIDDEN_PORT",
    }
    for key, value in replacements.items():
        message = message.replace(str(key), value)
    return message


async def async_delete_dir(path: str) -> None:
    """Asynchronously delete a directory and its contents."""
    try:
        await asyncio.to_thread(shutil.rmtree, path)
    except FileNotFoundError:
        pass


async def async_scandir(directory: str) -> AsyncIterator[os.DirEntry[str]]:
    for entry in os.scandir(directory):
        yield entry


async def async_zip_directory(output_filename: str, directory: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, zip_directory, output_filename, directory)


def zip_directory(output_filename: str, directory: str) -> None:
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(directory):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(
                        os.path.join(root, file), os.path.join(directory, "..")
                    ),
                )


def execute_cmd(cmd: str) -> None:
    subprocess.run(cmd, shell=True, check=True)


async def async_run_command(cmd: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, execute_cmd, cmd)


async def check_file_size(file: UploadFile, max_size: int) -> bool:
    """
    Check the size of an uploaded file without reading it entirely into memory.
    Returns True if the file is within the allowed size, otherwise raises an HTTPException.
    """
    total_size = 0
    chunk_size = 128 * 1024  # 128KB

    while data := await file.read(chunk_size):
        total_size += len(data)
        if total_size > max_size:
            return False

    await file.seek(0)  # Reset file position for further processing if needed
    return True


def search_value(d: dict[str, Any], target: Any) -> str:
    for key, value in d.items():
        if value == target:
            return key
    raise ValueError(f"{target} is not in the dictionary")


def next_column_name(attribute_mapping: dict[str, Any], data_type: str) -> str:
    attributes = attribute_mapping.keys()
    # Regular expression to find attributes with the given data type and a number
    pattern = re.compile(rf"^{data_type}_attr(\d+)$")

    # Find all numbers for the given data type attributes
    numbers = [
        int(match.group(1)) for attr in attributes if (match := pattern.match(attr))
    ]

    # Determine the next number (increment the highest found number)
    next_number = max(numbers) + 1 if numbers else 1

    # Construct the new attribute name
    return f"{data_type}_attr{next_number}"


def get_result_column(
    attribute_mapping: dict[str, Any], base_column_name: str, datatype: str
) -> dict[str, str]:
    # Initialize the highest number found for the column name
    highest_num = 0
    base_name_exists = False

    # Regular expression pattern to find numbered columns
    pattern = re.compile(rf"^{base_column_name}_(\d+)$")

    # Check all existing column names
    for column_name in attribute_mapping.values():
        if column_name == base_column_name:
            # Base name exists without any number
            base_name_exists = True
        else:
            # Match the pattern to find numbered columns
            match = pattern.match(column_name)
            if match:
                # Extract the number and update highest_num if this number is larger
                num = int(match.group(1))
                if num > highest_num:
                    highest_num = num
    mapped_column = next_column_name(attribute_mapping, datatype)
    # Construct the new column name based on the findings
    if base_name_exists or highest_num > 0:
        return {mapped_column: f"{base_column_name}_{highest_num + 1}"}
    else:
        # If the base name and no numbered variants were found, return the base name
        return {mapped_column: base_column_name}


def build_where(
    id: UUID,
    table_name: str,
    query: None | str | CQLQueryObject,
    attribute_mapping: dict[str, Any],
    return_basic_filter: bool = True,
) -> str | None:
    """Builds a PostgreSQL WHERE clause based on a CQL query and layer ID."""

    if query is None:
        if return_basic_filter:
            return f"{table_name}.layer_id = '{str(id)}'"
        return None
    else:
        if isinstance(query, str):
            query_dict = {"cql": json.loads(query)}
        else:
            query_dict = {"cql": query.cql}

        query_obj = CQLQuery(query=query_dict)
        assert query_obj.query is not None
        ast = cql2_json_parser(query_obj.query.cql)
        attribute_mapping = {value: key for key, value in attribute_mapping.items()}
        # Add id to attribute mapping
        attribute_mapping["id"] = "id"
        attribute_mapping["geometry"] = "geom"
        attribute_mapping["geom"] = "geom"
        where = f"{table_name}.layer_id = '{str(id)}' AND "
        converted_cql = to_sql_where(ast, attribute_mapping)
        converted_cql = re.sub(r'(?<=\(|\s|,)"', f'{table_name}."', converted_cql)
        # Fixing issue with pygeofilter https://github.com/geopython/pygeofilter/pull/54
        converted_cql = converted_cql.replace(
            "ST_GeomFromWKB(x'", "ST_GeomFromWKB(E'\\\\x"
        )
        # Add SRID to ST_GeomFromWKB otherwise it will be 0 and operations won't work
        converted_cql = re.sub(
            r"(ST_GeomFromWKB\((.*?)\))", r"ST_SetSRID(\1, 4326)", converted_cql
        )
        where = where + converted_cql
        # Cast all columns subject to a likeliness check to TEXT, ensuring it succeeds
        where = re.sub(
            r'("([^"]*)")(?=\s+LIKE)',
            r"\1::TEXT",
            where,
        )
        where = where.replace("LIKE", "ILIKE")
        return where


def build_where_clause(queries: list[str]) -> str:
    # Remove none values from queries
    queries = [query for query in queries if query is not None]
    if len(queries) == 0:
        return ""
    elif len(queries) == 1:
        return "WHERE " + queries[0]
    else:
        return "WHERE " + " AND ".join(queries)


def build_insert_query(
    read_table_name: str,
    result_table_name: str,
    attribute_mapping: dict[str, Any],
    result_column: str = "",
) -> tuple[str, str]:
    # Create insert statement
    insert_columns = ", ".join(attribute_mapping.keys())
    if result_column:
        insert_columns += ", " + result_column
    select_columns = ", ".join(
        f"{read_table_name}." + value
        for value in ["geom"] + list(attribute_mapping.keys())
    )
    insert_statement = (
        f"INSERT INTO {result_table_name} (layer_id, geom, {insert_columns})"
    )
    return insert_statement, select_columns


async def async_get_with_retry(
    url: str, headers: dict[str, str], num_retries: int, retry_delay: int
) -> str | None:
    async with aiohttp.ClientSession() as session:
        for i in range(num_retries):
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    # Server is still processing request, retry shortly
                    if i == num_retries - 1:
                        raise Exception(
                            "GEOAPI-Server took too long to process request. It can be that the layer is not properly processed yet."
                        )
                    await asyncio.sleep(retry_delay)
                    continue
                elif response.status == 200:
                    # Server has finished processing request, break
                    result = await response.text()
                    return result
                else:
                    raise Exception(await response.text())
    return None


def hex_to_rgb(hex: str) -> tuple[int, ...]:
    hex = hex.lstrip("#")
    return tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))


def without_keys(d: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """
    Omit keys from a dict
    """
    return {x: d[x] for x in d if x not in keys}


def to_feature_collection(
    sql_result: Any,
    geometry_name: str = "geom",
    geometry_type: str = "wkb",
    exclude_properties: list[str] = [],
) -> FeatureCollection:
    """
    Generic method to convert sql result to geojson. Geometry field is expected to be in geojson or postgis hex format.
    """
    if not isinstance(sql_result, list):
        sql_result = [sql_result]

    exclude_properties.append(geometry_name)
    features = []
    for row in sql_result:
        if not isinstance(row, dict):
            dict_row = dict(row)
        else:
            dict_row = row
        geometry = None
        if geometry_type == "wkb":
            geometry = to_shape(dict_row[geometry_name])
        elif geometry_type == "geojson":
            geometry = geojsonloads(dict_row[geometry_name])

        features.append(
            Feature(
                id=dict_row.get("gid") or dict_row.get("id") or 0,
                geometry=geometry,
                properties=without_keys(dict_row, exclude_properties),
            )
        )
    return FeatureCollection(features)


def format_value_null_sql(value: Any) -> str:
    if value is None:
        return "NULL"
    else:
        return f"'{value}'"


def sanitize_filename(name: str) -> str:
    # Extract just the file name (no paths)
    name = os.path.basename(name)
    # Allow only safe chars
    name = re.sub(r"[^a-zA-Z0-9._()\-\s]", "_", name)
    return name
