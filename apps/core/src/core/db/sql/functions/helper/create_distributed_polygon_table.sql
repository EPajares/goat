DROP FUNCTION IF EXISTS basic.create_distributed_polygon_table; 
CREATE OR REPLACE FUNCTION basic.create_distributed_polygon_table(
	input_table text, input_layer_project_id int, relevant_columns text, customer_schema text,
	scenario_id text, where_filter text, max_vertices_polygon integer, result_table_name text
)
RETURNS SETOF void
LANGUAGE plpgsql
AS $function$
BEGIN

	-- Create temporary table for polygons
	EXECUTE format(
		'DROP TABLE IF EXISTS polygons;
		CREATE TEMP TABLE polygons AS SELECT id, geom %s
		FROM (
            WITH scenario_features AS (
                SELECT sf.feature_id AS id, sf.geom, sf.edit_type %s
                FROM %s.scenario_scenario_feature ssf
                INNER JOIN %s.scenario_feature sf ON sf.id = ssf.scenario_feature_id
                WHERE ssf.scenario_id = %L
                AND sf.layer_project_id = %s
            )
                SELECT original_features.id, original_features.geom %s
                FROM (SELECT * FROM %s %s) original_features
                LEFT JOIN (SELECT id FROM scenario_features) sf ON original_features.id = sf.id
                WHERE sf.id IS NULL
            UNION ALL
                SELECT scenario_features.id, scenario_features.geom %s
                FROM scenario_features
                WHERE edit_type IN (''n'', ''m'')
        ) input_features;',
		relevant_columns, relevant_columns, customer_schema, customer_schema,
		scenario_id, input_layer_project_id, relevant_columns, input_table,
		where_filter, relevant_columns
	);
	
	-- Create subdivided polygon table and add GIST index
	EXECUTE format(
		'DROP TABLE IF EXISTS polygons_subdivided; 
		CREATE TEMP TABLE polygons_subdivided AS 
		WITH splitted AS 
		(
			SELECT id, ST_SUBDIVIDE(ST_MAKEVALID(geom), %s) AS geom %s
			FROM polygons
		)
		SELECT id, 
		CASE WHEN ST_IsValid(geom) = TRUE
		THEN geom
		ELSE ST_MakeValid(geom)
		END AS geom %s
		FROM splitted;', max_vertices_polygon, relevant_columns, relevant_columns
	);
	CREATE INDEX ON polygons_subdivided USING GIST(geom);
	
	-- Identify grids ids and their respective geometries
	DROP TABLE IF EXISTS h3_3_grids_uuid; 
	CREATE TEMP TABLE h3_3_grids_uuid AS 
	WITH h3_3_ids AS 
	(
		SELECT DISTINCT basic.fill_polygon_h3(geom, 3) AS h3_index
		FROM polygons 
	)
	SELECT basic.to_short_h3_3(h3_index::bigint) AS h3_3, ST_SETSRID(h3_cell_to_boundary(h3_index)::geometry, 4326) AS geom, 
	ST_Exteriorring(ST_SETSRID(h3_cell_to_boundary(h3_index)::geometry, 4326)) AS border 
	FROM h3_3_ids;  
	CREATE INDEX ON h3_3_grids_uuid USING GIST(geom); 
	CREATE INDEX ON h3_3_grids_uuid USING GIST(border); 
	
	
	-- Create empty distributed table 
	EXECUTE format(
		'DROP TABLE IF EXISTS %s;
		CREATE TABLE %s AS SELECT id, geom, NULL::INTEGER AS h3_3 %s
		FROM polygons_subdivided
		LIMIT 0;', 
		result_table_name, result_table_name, relevant_columns
	);
	-- Make table distributed
	PERFORM create_distributed_table(result_table_name, 'h3_3'); 
	
	-- Assign h3 grid id to the intersecting polygons. Split polygons add border where necessary.
	EXECUTE format(
		'INSERT INTO %s 
		SELECT s.id, ST_INTERSECTION(g.geom, s.geom) AS geom, g.h3_3 AS h3_3 %s
		FROM h3_3_grids_uuid g, polygons_subdivided s 
		WHERE ST_Intersects(g.border, s.geom)
		UNION ALL 
		SELECT s.id, s.geom, g.h3_3 %s
		FROM h3_3_grids_uuid g, polygons_subdivided s 
		WHERE ST_WITHIN(s.geom, g.geom)
		AND ST_Intersects(s.geom, g.geom)', 
		result_table_name, relevant_columns, relevant_columns
	); 

	-- Add GIST index 
	EXECUTE format('CREATE INDEX ON %s USING GIST(h3_3, geom)', result_table_name);
END;
$function$ 
PARALLEL SAFE;

/*
EXPLAIN ANALYZE 
SELECT basic.create_distributed_polygon_table(
	'user_data.polygon_744e4fd1685c495c8b02efebce875359', 
	'text_attr1',
	'WHERE layer_id = ''4bdbed8f-4804-4913-9b42-c547e7be0fd5'' AND text_attr1=''Niedersachsen''',
	30,
	'temporal.test'
)
*/
