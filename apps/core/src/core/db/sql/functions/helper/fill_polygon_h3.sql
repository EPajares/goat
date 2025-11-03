DROP FUNCTION IF EXISTS basic.fill_polygon_h3; 
CREATE OR REPLACE FUNCTION basic.fill_polygon_h3(geom geometry, h3_resolution integer)
RETURNS SETOF h3index
LANGUAGE plpgsql
AS $function$
BEGIN
	RETURN query 
	WITH border_points AS 
	(
		SELECT ((ST_DUMPPOINTS(geom)).geom)::point AS geom
	),
	polygons AS 
	(
		SELECT ((ST_DUMP(geom)).geom)::polygon AS geom
	),
	h3_ids AS 
	(
		SELECT h3_lat_lng_to_cell(b.geom, h3_resolution) h3_index
		FROM border_points b
		UNION ALL 
		SELECT h3_polygon_to_cells(p.geom, ARRAY[]::polygon[], h3_resolution) h3_index
		FROM polygons p
	)
	SELECT DISTINCT h3_index
	FROM h3_ids; 
END;
$function$ 
PARALLEL SAFE;
