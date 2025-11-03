import io
import json
import random
from typing import Any, Dict, List, Union
from urllib.parse import quote

import aiohttp
import matplotlib.pyplot as plt
import pandas as pd
from cairosvg import svg2png
from PIL import Image
from pydantic import BaseModel
from pymgl import Map
from shapely import from_wkb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from core.core.config import settings
from core.db.models import Project
from core.db.models.layer import Layer, LayerType
from core.schemas.layer import FeatureType
from core.schemas.project import InitialViewState
from core.utils import async_get_with_retry

basemaps = {
    "streets": "mapbox://styles/mapbox/streets-v12",
    "satellite": "mapbox://styles/mapbox/satellite-v9",
    "light": "mapbox://styles/mapbox/light-v11",
    "dark": "mapbox://styles/mapbox/dark-v11",
}


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def get_mapbox_style_color(data: Dict, type: str) -> Union[str, List]:
    colors = data["properties"].get(f"{type}_range", {}).get("colors")
    field_name = data["properties"].get(f"{type}_field", {}).get("name")
    color_scale = data["properties"].get(f"{type}_scale")
    color_maps = data["properties"].get(f"{type}_range", {}).get("color_map")

    # Assuming fieldType is defined somewhere, similar to the TypeScript version
    field_type = data["properties"].get(f"{type}_field", {}).get("type")
    if (
        color_maps
        and field_name
        and isinstance(color_maps, list)
        and color_scale == "ordinal"
    ):
        values_and_colors = []
        for color_map in color_maps:
            color_map_value = color_map[0]
            color_map_hex = color_map[1]
            if not color_map_value or not color_map_hex:
                continue
            if isinstance(color_map_value, list):
                for value in color_map_value:
                    if field_type == "number" and value is not None:
                        try:
                            numeric_value = float(value)  # Convert to number
                            values_and_colors.append(numeric_value)
                        except ValueError:
                            # Handle the case where conversion is not possible
                            values_and_colors.append(value)
                    else:
                        values_and_colors.append(value)
                    values_and_colors.append(color_map_hex)
            else:
                if field_type == "number" and color_map_value is not None:
                    try:
                        numeric_value = float(color_map_value)  # Convert to number
                        values_and_colors.append(numeric_value)
                    except ValueError:
                        # Handle the case where conversion is not possible
                        values_and_colors.append(color_map_value)
                else:
                    values_and_colors.append(color_map_value)
                values_and_colors.append(color_map_hex)

        return ["match", ["get", field_name]] + values_and_colors + ["#AAAAAA"]

    if (
        not field_name
        or not colors
        or len(data["properties"].get(f"{type}_scale_breaks", {}).get("breaks", []))
        != len(colors) - 1
    ):
        return (
            rgb_to_hex(data["properties"].get(type))
            if data["properties"].get(type)
            else "#000000"
        )

    color_steps = []
    for index, color in enumerate(colors):
        if index == len(colors) - 1:
            color_steps.append([colors[index]])
        else:
            color_steps.append(
                [
                    color,
                    data["properties"]
                    .get(f"{type}_scale_breaks", {})
                    .get("breaks", [])[index]
                    or 0,
                ]
            )

    config = ["step", ["get", field_name]] + [
        item for sublist in color_steps for item in sublist
    ]
    return config


def get_mapbox_style_marker(data: dict) -> str | List[Any]:
    properties = data["properties"]
    marker_maps = properties.get("marker_mapping")
    field_name = properties.get("marker_field", {}).get("name")
    marker = f"{settings.MARKER_PREFIX}{properties.get('marker', {}).get('name')}"
    if marker_maps and field_name:
        values_and_icons = []
        icon_set = set()
        for marker_map in marker_maps:
            marker_map_value = marker_map[0]
            marker_map_icon = marker_map[1]
            if not marker_map_value or not marker_map_icon:
                continue
            if isinstance(marker_map_value, list):
                for value in marker_map_value:
                    values_and_icons.append(value)
                    icon = f"{settings.MARKER_PREFIX}{marker_map_icon['name']}"
                    values_and_icons.append(icon)
                    icon_set.add(icon)
            else:
                values_and_icons.append(marker_map_value)
                icon = f"{settings.MARKER_PREFIX}{marker_map_icon['name']}"
                values_and_icons.append(icon)
                icon_set.add(icon)

        # Set the icons
        properties["marker"] = list(icon_set)

        return ["match", ["get", field_name], *values_and_icons, marker]

    return marker


def transform_to_mapbox_layer_style_spec(data: dict) -> dict:
    type = data.get("feature_layer_geometry_type")
    if type == "point":
        point_properties = data.get("properties")
        # Check if there is a marker field
        if point_properties.get("custom_marker") is True:
            style = {
                "type": "symbol",
                "layout": {
                    "icon-image": get_mapbox_style_marker(data),
                    "icon-size": point_properties["radius"],
                },
                "paint": {
                    "icon-opacity": point_properties.get("opacity", 0),
                    "icon-color": get_mapbox_style_color(data, "color"),
                },
            }
        else:
            style = {
                "type": "circle",
                "paint": {
                    "circle-color": get_mapbox_style_color(data, "color"),
                    "circle-opacity": point_properties.get("filled", False)
                    * point_properties.get("opacity", 0),
                    "circle-radius": point_properties.get("radius", 5),
                    "circle-stroke-color": get_mapbox_style_color(data, "stroke_color"),
                    "circle-stroke-width": point_properties.get("stroked", False)
                    * point_properties.get("stroke_width", 1),
                },
            }
        return style

    elif type == "polygon":
        polygon_properties = data.get("properties")
        return {
            "type": "fill",
            "paint": {
                "fill-color": get_mapbox_style_color(data, "color"),
                "fill-opacity": polygon_properties.get("filled", False)
                * polygon_properties.get("opacity", 0),
                "fill-outline-color": get_mapbox_style_color(data, "stroke_color"),
                "fill-antialias": polygon_properties.get("stroked", False),
            },
        }
    elif type == "line":
        line_properties = data.get("properties")
        return {
            "type": "line",
            "paint": {
                "line-color": get_mapbox_style_color(data, "stroke_color"),
                "line-opacity": line_properties.get("opacity", 0),
                "line-width": line_properties.get("stroke_width", 1),
            },
        }
    else:
        raise ValueError(f"Invalid type: {type}")


class PrintMap:
    def __init__(self, async_session: AsyncSession) -> None:
        self.thumbnail_zoom = 13
        self.thumbnail_height = 280
        self.thumbnail_width = 674
        self.async_session = async_session

    async def add_icons_to_map(self, map: Map, layer: Layer) -> Map:
        """Add icons to map."""

        # Request icon from assets url
        marker_size = layer.properties["marker_size"]

        # Check if marker mapping exists then add all markers to map
        markers = []
        if not layer.properties.get("marker_mapping"):
            marker = layer.properties.get("marker")
            markers.append(
                {
                    "name": f"{settings.MARKER_PREFIX}{marker['name']}",
                    "url": marker["url"],
                }
            )
        else:
            for marker in layer.properties.get("marker_mapping"):
                markers.append(
                    {
                        "name": f"{settings.MARKER_PREFIX}{marker[0][0]}",
                        "url": marker[1]["url"],
                    }
                )

        async with aiohttp.ClientSession() as session:
            # for marker in layer.properties.get("marker"):
            for marker in markers:
                icon_url = marker["url"]
                icon_name = marker["name"]
                try:
                    header = (
                        {"Content-Type": "image/svg+xml"}
                        if icon_url.endswith(".svg")
                        else {"Content-Type": "image/png"}
                    )
                    # Get icon
                    response = await session.get(icon_url, headers=header)
                    icon = await response.read()

                    # If icon is svg convert to png
                    if icon_url.endswith(".svg"):
                        icon = svg2png(
                            bytestring=icon,
                            output_height=marker_size,
                            output_width=marker_size,
                        )
                    elif not icon_url.endswith(".png"):
                        raise ValueError("Invalid icon type.")
                    # Save image to local dir
                    with open(f"{icon_name}.png", "wb") as f:
                        f.write(icon)
                    # # Open the image and get raw pixel data
                    image = Image.open(io.BytesIO(icon))
                    icon = image.tobytes()
                    # Add icon to map
                    map.addImage(icon_name, icon, marker_size, marker_size, 1.0, True)
                except Exception as e:
                    print(f"Error while adding icon to map: {e}")
        return map

    async def create_layer_thumbnail(self, layer: Layer, file_name: str) -> str:
        """Create layer thumbnail."""
        # Check layer type
        if layer.type == LayerType.table:
            image = await self.create_table_thumbnail(layer)
        elif layer.type == LayerType.raster:
            image = await self.create_raster_layer_thumbnail(layer)
        elif (
            layer.type == LayerType.feature
            and layer.feature_layer_type != FeatureType.street_network
        ):
            image = await self.create_feature_layer_thumbnail(layer)
        else:
            raise ValueError("Invalid layer type.")

        # Save image to s3 bucket using s3 client from settings
        dir = settings.THUMBNAIL_DIR_LAYER + "/" + file_name
        url = settings.ASSETS_URL + "/" + dir

        # Save to s3
        settings.S3_CLIENT.upload_fileobj(
            Fileobj=image,
            Bucket=settings.AWS_S3_ASSETS_BUCKET,
            Key=dir,
            ExtraArgs={"ContentType": "image/png"},
            Callback=None,
            Config=None,
        )
        return url

    async def create_raster_layer_thumbnail(self, layer: Layer) -> io.BytesIO:
        """Create raster layer thumbnail."""

        # Define map
        map = Map(basemaps["light"], provider="mapbox", token=settings.MAPBOX_TOKEN)
        map.load()

        # Set map extent
        if layer.extent and layer.extent.data:
            geom_shape = from_wkb(layer.extent.data)
            xmin, ymin, xmax, ymax = geom_shape.bounds
        else:
            # Define global extent
            xmin, ymin, xmax, ymax = -180.0, -90.0, 180.0, 90.0

        map.setBounds(
            xmin=xmin,
            ymin=ymin,
            xmax=xmax,
            ymax=ymax,
        )
        map.setSize(self.thumbnail_width, self.thumbnail_height)

        map.addSource(
            layer.name,
            json.dumps(
                {
                    "type": "raster",
                    "tileSize": getattr(layer, "other_properties", {}).get(
                        "tileSize", 256
                    ),
                    "tiles": [layer.url],
                }
            ),
        )
        # Add layer
        map.addLayer(
            json.dumps(
                {
                    "id": layer.name,
                    "type": "raster",
                    "source": layer.name,
                    "source-layer": "default",
                    "layout": {
                        "visibility": "visible",
                    },
                    "paint": {
                        "raster-opacity": layer.properties.get("opacity", 1),
                    },
                }
            )
        )

        img_bytes = map.renderPNG()
        image = io.BytesIO(img_bytes)
        return image

    async def create_feature_layer_thumbnail(self, layer: Layer) -> io.BytesIO:
        """Create feature layer thumbnail."""

        # Define map
        map = Map(basemaps["light"], provider="mapbox", token=settings.MAPBOX_TOKEN)
        map.load()

        # Set map extent
        geom_shape = from_wkb(layer.extent.data)
        map.setBounds(
            xmin=geom_shape.bounds[0],
            ymin=geom_shape.bounds[1],
            xmax=geom_shape.bounds[2],
            ymax=geom_shape.bounds[3],
        )
        map.setSize(self.thumbnail_width, self.thumbnail_height)

        # Transform layer to mapbox style
        style = transform_to_mapbox_layer_style_spec(layer.dict())

        # Add icons to map in case of icon style
        if style["type"] == "symbol":
            map = await self.add_icons_to_map(map, layer)

        # Get collection id
        layer_id = layer.id
        collection_id = "user_data." + str(layer_id).replace("-", "")

        # Request in recursive loop if layer was already added in geoapi if it does not fail the layer was added
        header = {"Content-Type": "application/json"}
        await async_get_with_retry(
            url=f"{settings.GOAT_GEOAPI_HOST}/collections/" + collection_id,
            headers=header,
            num_retries=10,
            retry_delay=1,
        )

        # Add layer source
        tile_url = (
            f"{settings.GOAT_GEOAPI_HOST}/collections/"
            + collection_id
            + "/tiles/{z}/{x}/{y}"
        )
        map.addSource(
            layer.name,
            json.dumps(
                {
                    "type": "vector",
                    "tiles": [tile_url],
                }
            ),
        )
        # Add layer
        layer = {
            "id": layer.name,
            "type": style["type"],
            "source": layer.name,
            "source-layer": "default",
            "paint": style["paint"],
        }
        if style.get("layout"):
            layer["layout"] = style["layout"]

        map.addLayer(json.dumps(layer))

        img_bytes = map.renderPNG()
        image = io.BytesIO(img_bytes)

        return image

    async def create_table_thumbnail(self, layer: Layer) -> io.BytesIO:
        """Create table thumbnail."""

        # Get the first 4 four columns of the attribute mapping.
        columns = []
        columns_mapped = []
        mixed_items = list(layer.attribute_mapping.items())
        random.shuffle(mixed_items)
        index = 0
        for key, value in mixed_items:
            index += 1
            if index < 5:
                columns.append(key)
                # Limit columns name to 5 chars and add ...
                if len(value) > 6:
                    value = value[:6] + "..."
                columns_mapped.append(value)

        # Read four rows of the table and create a DataFrame
        data = await self.async_session.execute(
            text(f"""
            SELECT {', '.join(columns[:4])}
            FROM {layer.table_name}
            LIMIT 4
            """)
        )
        data = data.all()
        # Add an empty row at end of each row
        data = [list(row) for row in data]
        data.append(["..."] * len(columns_mapped[:4]))

        # Limit the length of the content of each cell to 15 chars and add ...
        for row in data:
            for index, cell in enumerate(row):
                if len(str(cell)) > 15:
                    row[index] = str(cell)[:15] + "..."

        # Create a DataFrame
        df = pd.DataFrame(data, columns=columns_mapped[:4])

        # If the len of the columns exceed 4 then add a column with ...
        if len(columns_mapped) > 4:
            df["... "] = "..."

        # Create a figure and an axes
        fig, ax = plt.subplots(
            figsize=(self.thumbnail_width / 80, self.thumbnail_height / 80)
        )  # Convert pixels to inches

        # Remove the axes
        ax.axis("off")

        # Create a table and add it to the axes
        table = plt.table(
            cellText=df.values,
            colLabels=df.columns,
            loc="center",
            cellLoc="center",
            colWidths=[1] * len(df.columns),  # Make columns of equal size
            bbox=[0, 0, 1, 1],  # Full height and width with a small padding
        )
        table.auto_set_font_size(False)
        table.set_fontsize(12)

        # Set the color, font weight, and font color of the header cells
        table_props = table.properties()
        table_cells = table_props["children"]
        color = "#535353"
        for cell in table_cells:
            if cell.get_text().get_text() in df.columns:
                cell.set_facecolor(color)
                cell.get_text().set_fontsize(16)
                cell.get_text().set_weight("bold")  # Make the text bold
                cell.get_text().set_color("white")  # Set the font color to white

        # Save the file as bytes and return it
        image = io.BytesIO()
        fig.savefig(image, bbox_inches="tight", pad_inches=1)
        image.seek(0)
        return image

    async def create_project_thumbnail(
        self,
        project: Project,
        initial_view_state: InitialViewState,
        layers_project: List[BaseModel],
        file_name: str,
    ) -> str:
        basemap = project.basemap
        style_url = None
        if not basemap:
            style_url = basemaps["strets"]
        elif basemaps.get(basemap):
            style_url = basemaps[basemap]
        else:
            style_url = basemaps["streets"]

        # Define map
        map = Map(style_url, provider="mapbox", token=settings.MAPBOX_TOKEN)
        map.load()

        # Set map extent
        map.setCenter(initial_view_state["longitude"], initial_view_state["latitude"])
        map.setZoom(initial_view_state["zoom"])
        map.setSize(self.thumbnail_width, self.thumbnail_height)

        # Sort layer_project by layer order
        if len(layers_project) > 1:
            layers_project.sort(
                key=lambda x: project.layer_order.index(x.id), reverse=True
            )

        for layer in layers_project:
            if (
                layer.properties["visibility"] is False
                or layer.properties["visibility"] is None
            ):
                continue

            if (
                layer.type == LayerType.feature
                and layer.feature_layer_type != FeatureType.street_network
            ):
                # Get collection id
                layer_id = layer.layer_id
                collection_id = "user_data." + str(layer_id).replace("-", "")

                # Request in recursive loop if layer was already added in geoapi if it does not fail the layer was added
                header = {"Content-Type": "application/json"}
                await async_get_with_retry(
                    url=f"{settings.GOAT_GEOAPI_HOST}/collections/" + collection_id,
                    headers=header,
                    num_retries=10,
                    retry_delay=1,
                )

                # Transform style
                style = transform_to_mapbox_layer_style_spec(layer.dict())

                cql_filter = ""

                if layer.query and layer.query.cql:
                    json_cql_str = json.dumps(layer.query.cql)
                    cql_filter = f"?filter={quote(json_cql_str)}"

                # Add layer source
                tile_url = (
                    f"{settings.GOAT_GEOAPI_HOST}/collections/"
                    + collection_id
                    + "/tiles/{z}/{x}/{y}"
                    + cql_filter
                )

                map.addSource(
                    layer.name,
                    json.dumps(
                        {
                            "type": "vector",
                            "tiles": [tile_url],
                        }
                    ),
                )
                # Add layer
                map.addLayer(
                    json.dumps(
                        {
                            "id": layer.name,
                            "type": style["type"],
                            "source": layer.name,
                            "source-layer": "default",
                            "paint": style["paint"],
                        }
                    )
                )
            elif layer.type == LayerType.raster:
                # Add raster layer source
                map.addSource(
                    layer.name,
                    json.dumps(
                        {
                            "type": "raster",
                            "tileSize": getattr(layer, "other_properties", {}).get(
                                "tileSize", 256
                            ),
                            "tiles": [layer.url],
                        }
                    ),
                )
                # Add raster layer
                map.addLayer(
                    json.dumps(
                        {
                            "id": layer.name,
                            "type": "raster",
                            "source": layer.name,
                            "source-layer": "default",
                            "layout": {
                                "visibility": "visible",
                            },
                            "paint": {
                                "raster-opacity": layer.properties.get("opacity", 1),
                            },
                        }
                    )
                )
        # img_bytes = map.renderPNG()
        try:
            img_bytes = map.renderPNG()
        except RuntimeError as e:
            print("Error while rendering PNG:", e)
            print("Map state:", map.getState())
            raise
        image = io.BytesIO(img_bytes)

        # Save image to s3 bucket using s3 client from settings
        dir = settings.THUMBNAIL_DIR_PROJECT + "/" + file_name
        url = settings.ASSETS_URL + "/" + dir

        # Save to s3
        settings.S3_CLIENT.upload_fileobj(
            Fileobj=image,
            Bucket=settings.AWS_S3_ASSETS_BUCKET,
            Key=dir,
            ExtraArgs={"ContentType": "image/png"},
            Callback=None,
            Config=None,
        )
        return url
