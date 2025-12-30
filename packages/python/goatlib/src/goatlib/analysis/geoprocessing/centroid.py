import logging
from pathlib import Path
from typing import List, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geoprocessing import CentroidParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class CentroidTool(AnalysisTool):
    """Tool for computing centroid of features.

    This tool computes the centroid of each feature in the input layer.
    """

    def _run_implementation(
        self: Self, params: CentroidParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform centroid operation.

        Args:
            params: CentroidParams object with input_path and other options.

        Returns:
            List containing tuple of (output_path, metadata).
        """
        # Import input dataset
        input_meta, input_view = self.import_input(params.input_path, "input_data")

        # Validate geometry columns
        input_geom = input_meta.geometry_column

        if not input_geom:
            raise ValueError(
                f"Could not detect geometry column for input: {params.input_path}"
            )

        # Validate geometry types
        self.validate_geometry_types(
            input_view, input_geom, params.accepted_input_geometry_types, "input"
        )

        # Define output path
        if not params.output_path:
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}_centroid.parquet"
            )
        output_path = Path(params.output_path)

        logger.info("Computing centroids")

        self.con.execute(f"""
            CREATE OR REPLACE VIEW centroid_result AS
            SELECT
                * EXCLUDE ({input_geom}),
                ST_Centroid({input_geom}) AS {input_geom}
            FROM {input_view}
        """)

        # Export view result to file
        self.con.execute(
            f"COPY centroid_result TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("Centroid data written to %s", output_path)

        # Create metadata for output
        output_metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            geometry_column=input_geom,
            crs="EPSG:4326",  # Assuming WGS84 as per ClipTool
            schema="public",
            table_name=output_path.stem,
        )

        return [(output_path, output_metadata)]
