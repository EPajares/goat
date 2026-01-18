"""
Geocoding Tool.

This module provides a tool for geocoding addresses using Pelias.
It reads addresses from a parquet file, geocodes them via Pelias free-text search,
and writes results back to a parquet file with the original attributes plus
geocoding results (geometry, confidence, match_type).
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, List, Self, Tuple

import httpx

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geocoding import (
    GeocodingParams,
    GeocodingResult,
)
from goatlib.io.parquet import write_optimized_parquet
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)

# Maximum number of features allowed for geocoding
MAX_FEATURES = 10000


class GeocodingTool(AnalysisTool):
    """
    Tool for geocoding addresses using Pelias.

    Reads addresses from a parquet file, geocodes each row via Pelias
    free-text search API, and writes results to a new parquet file
    containing the original attributes plus geocoding results.

    Example:
        tool = GeocodingTool()
        results = tool.run(GeocodingParams(
            input_path="/data/addresses.parquet",
            input_mode=GeocodingInputMode.full_address,
            full_address_field="address",
            output_path="/data/geocoded.parquet",
            geocoder_url="https://geocoder.example.com",
            geocoder_username="admin",
            geocoder_password="secret",
        ))
        # results is a List[Tuple[Path, DatasetMetadata]]
    """

    # Default HTTP settings
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CONCURRENT_REQUESTS = 10

    def __init__(
        self: Self,
        timeout: float = DEFAULT_TIMEOUT,
        concurrent_requests: int = DEFAULT_CONCURRENT_REQUESTS,
        db_path: Path | None = None,
    ) -> None:
        """
        Initialize the geocoding tool.

        Args:
            timeout: HTTP request timeout in seconds
            concurrent_requests: Max concurrent geocoding requests
            db_path: Optional path to a DuckDB database file
        """
        super().__init__(db_path=db_path)
        self._timeout = timeout
        self._concurrent_requests = concurrent_requests

    def _run_implementation(
        self: Self, params: GeocodingParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """
        Execute geocoding.

        Args:
            params: Geocoding parameters

        Returns:
            List containing tuple of (output_path, metadata)

        Raises:
            ValueError: If input has more than MAX_FEATURES rows
        """
        logger.info(
            "Starting geocoding: input=%s, mode=%s",
            params.input_path,
            params.input_mode.value,
        )

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        output_path = loop.run_until_complete(self._run_async(params))

        # Return in the standard format with DatasetMetadata
        return [
            (
                output_path,
                DatasetMetadata(
                    path=str(output_path),
                    source_type="vector",
                    format="geoparquet",
                    geometry_type="Point",
                    crs="EPSG:4326",
                ),
            ),
        ]

    async def _run_async(self: Self, params: GeocodingParams) -> Path:
        """Async implementation of geocoding."""
        # Read input parquet and check row count
        self.con.execute(
            f"CREATE VIEW input_data AS SELECT * FROM read_parquet('{params.input_path}')"
        )
        row_count = self.con.execute("SELECT COUNT(*) FROM input_data").fetchone()[0]

        if row_count > MAX_FEATURES:
            raise ValueError(
                f"Input has {row_count} rows, but maximum allowed is {MAX_FEATURES}"
            )

        logger.info("Read %d rows from %s", row_count, params.input_path)

        # Get column names and data as list of dicts
        columns = [col[0] for col in self.con.execute("DESCRIBE input_data").fetchall()]
        rows = self.con.execute("SELECT * FROM input_data").fetchall()
        row_dicts = [dict(zip(columns, row)) for row in rows]

        # Prepare geocoding requests
        authorization = params.geocoder_authorization
        search_url = f"{params.geocoder_url}/v1/search"

        # Geocode all rows with concurrency control
        semaphore = asyncio.Semaphore(self._concurrent_requests)
        results: list[GeocodingResult] = []

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            tasks = []
            for row in row_dicts:
                query_text = params.build_query_text(row)
                task = self._geocode_address(
                    client, search_url, query_text, authorization, semaphore
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

        logger.info("Geocoded %d addresses", len(results))

        # Build output with DuckDB
        output_path = self._write_output(results, params.output_path)

        logger.info("Wrote geocoding results to %s", output_path)
        return output_path

    async def _geocode_address(
        self: Self,
        client: httpx.AsyncClient,
        url: str,
        query_text: str,
        authorization: str,
        semaphore: asyncio.Semaphore,
    ) -> GeocodingResult:
        """
        Geocode a single address.

        Args:
            client: HTTP client
            url: Pelias search endpoint URL
            query_text: Address text to geocode
            authorization: Authorization header value
            semaphore: Concurrency control semaphore

        Returns:
            GeocodingResult with geocoded coordinates or None values if failed
        """
        async with semaphore:
            headers = {"Authorization": authorization}

            try:
                response = await client.get(
                    url,
                    params={"text": query_text, "size": 1},
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.warning(
                        "Geocoding failed for '%s': %s",
                        query_text,
                        response.status_code,
                    )
                    return GeocodingResult(input_text=query_text)

                data = response.json()
                return self._parse_pelias_response(query_text, data)

            except Exception as e:
                logger.warning("Geocoding error for '%s': %s", query_text, e)
                return GeocodingResult(input_text=query_text)

    def _parse_pelias_response(
        self: Self,
        query_text: str,
        data: dict[str, Any],
    ) -> GeocodingResult:
        """
        Parse Pelias GeoJSON response.

        Args:
            query_text: Original query text
            data: Pelias API response (GeoJSON FeatureCollection)

        Returns:
            GeocodingResult with parsed data
        """
        features = data.get("features", [])

        if not features:
            return GeocodingResult(input_text=query_text)

        feature = features[0]
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})

        # Extract coordinates (GeoJSON is [lon, lat])
        coords = geometry.get("coordinates", [])
        longitude = coords[0] if len(coords) > 0 else None
        latitude = coords[1] if len(coords) > 1 else None

        # Extract confidence and match type
        confidence = properties.get("confidence")
        match_type = properties.get("match_type")

        return GeocodingResult(
            input_text=query_text,
            latitude=latitude,
            longitude=longitude,
            confidence=confidence,
            match_type=match_type,
        )

    def _write_output(
        self: Self,
        results: list[GeocodingResult],
        output_path: str,
    ) -> Path:
        """
        Write geocoding results to parquet file.

        Combines original data with geocoding results, adding geometry column.

        Args:
            results: List of geocoding results
            output_path: Path for output file

        Returns:
            Path to the written file
        """
        # Create a temporary table with geocoding results
        self.con.execute("""
            CREATE TEMP TABLE geocode_results (
                row_id INTEGER,
                geocode_input_text VARCHAR,
                geocode_latitude DOUBLE,
                geocode_longitude DOUBLE,
                geocode_confidence DOUBLE,
                geocode_match_type VARCHAR
            )
        """)

        # Insert results
        for idx, result in enumerate(results):
            self.con.execute(
                """
                INSERT INTO geocode_results VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    idx,
                    result.input_text,
                    result.latitude,
                    result.longitude,
                    result.confidence,
                    result.match_type,
                ],
            )

        # Join original data with results and create geometry
        self.con.execute("""
            CREATE TEMP TABLE output_data AS
            SELECT
                i.*,
                g.geocode_input_text,
                g.geocode_latitude,
                g.geocode_longitude,
                g.geocode_confidence,
                g.geocode_match_type,
                CASE
                    WHEN g.geocode_latitude IS NOT NULL AND g.geocode_longitude IS NOT NULL
                    THEN ST_Point(g.geocode_longitude, g.geocode_latitude)
                    ELSE NULL
                END AS geometry
            FROM (SELECT *, ROW_NUMBER() OVER () - 1 AS _row_id FROM input_data) i
            LEFT JOIN geocode_results g ON i._row_id = g.row_id
        """)

        # Remove the temporary _row_id column
        columns = [
            col[0]
            for col in self.con.execute("DESCRIBE output_data").fetchall()
            if col[0] != "_row_id"
        ]
        columns_str = ", ".join(columns)

        # Ensure output directory exists
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to parquet
        write_optimized_parquet(
            self.con,
            f"SELECT {columns_str} FROM output_data",
            output_path,
            geometry_column="geometry",
        )

        return path
