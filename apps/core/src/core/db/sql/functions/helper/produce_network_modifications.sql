DROP FUNCTION IF EXISTS basic.produce_network_modifications;
CREATE OR REPLACE FUNCTION basic.produce_network_modifications(
	scenario_id_input UUID,
	edge_layer_project_id INTEGER,
	node_layer_project_id INTEGER
)
RETURNS TEXT
LANGUAGE plpgsql
AS $function$
DECLARE
	network_modifications_table TEXT;

	edge_layer_id UUID := (SELECT layer_id FROM customer.layer_project WHERE id = edge_layer_project_id);
	edge_network_table TEXT := 'user_data.street_network_line_' || REPLACE((
		SELECT user_id FROM customer.layer WHERE id = edge_layer_id
	)::TEXT, '-', '');
	node_layer_id UUID := (SELECT layer_id FROM customer.layer_project WHERE id = node_layer_project_id);
	node_network_table TEXT := 'user_data.street_network_point_' || REPLACE((
		SELECT user_id FROM customer.layer WHERE id = node_layer_id
	)::TEXT, '-', '');

   cnt integer;
   rec record;

   max_node_id integer;
   max_node_id_increment integer := 1;
   max_edge_id integer;
   max_edge_id_increment integer := 1;
BEGIN
	---------------------------------------------------------------------------------------------------------------------
	--Proceed only if the scenario contains features which apply to the specified edge layer
	---------------------------------------------------------------------------------------------------------------------
	
	IF NOT EXISTS (
		SELECT 1
		FROM customer.scenario_scenario_feature ssf
		INNER JOIN customer.scenario_feature sf ON sf.id = ssf.scenario_feature_id
		WHERE ssf.scenario_id = scenario_id_input
		AND sf.layer_project_id = edge_layer_project_id
	) THEN
		RETURN NULL;
	END IF;

	-- Create network modifications table
	SELECT 'temporal.network_modifications_' || basic.uuid_generate_v7() INTO network_modifications_table;
	EXECUTE FORMAT('
		DROP TABLE IF EXISTS %I;
		CREATE TABLE %I (
			edit_type TEXT, id INTEGER, class_ TEXT, source INTEGER,
			target INTEGER, length_m FLOAT8, length_3857 FLOAT8,
			coordinates_3857 JSONB, impedance_slope FLOAT8,
			impedance_slope_reverse FLOAT8, impedance_surface FLOAT8,
			maxspeed_forward INTEGER, maxspeed_backward INTEGER,
			geom GEOMETRY(LINESTRING, 4326), h3_6 INTEGER, h3_3 INTEGER
		);
	', network_modifications_table, network_modifications_table);

	---------------------------------------------------------------------------------------------------------------------
	--Prepare Table
	---------------------------------------------------------------------------------------------------------------------

	EXECUTE FORMAT('SELECT max(node_id) FROM %s;', node_network_table) INTO max_node_id;
	EXECUTE FORMAT('SELECT max(edge_id) FROM %s;', edge_network_table) INTO max_edge_id;

    DROP TABLE IF EXISTS modified_attributes_only;
	EXECUTE FORMAT('
		CREATE TEMP TABLE modified_attributes_only AS 
		SELECT w.*, e.edge_id AS original_id
		FROM %s e, (
			SELECT sf.*
			FROM customer.scenario_scenario_feature ssf
			INNER JOIN customer.scenario_feature sf ON sf.id = ssf.scenario_feature_id
			WHERE ssf.scenario_id = %L
			AND sf.layer_project_id = %s
		) w 
		WHERE e.h3_3 = w.h3_3
		AND e.id = w.feature_id 
		AND ST_ASTEXT(ST_ReducePrecision(w.geom,0.00001)) = ST_ASTEXT(ST_ReducePrecision(e.geom,0.00001))
		AND edit_type = ''m'';
	', edge_network_table, scenario_id_input, edge_layer_project_id);
	CREATE INDEX ON modified_attributes_only USING GIST(geom);

    DROP TABLE IF EXISTS drawn_features; 
	EXECUTE FORMAT('
		CREATE TEMP TABLE drawn_features AS
		WITH scenario_features AS (
			SELECT sf.*, ssf.scenario_id
			FROM customer.scenario_scenario_feature ssf
			INNER JOIN customer.scenario_feature sf ON sf.id = ssf.scenario_feature_id
			WHERE ssf.scenario_id = %L
			AND sf.layer_project_id = %s
			AND sf.edit_type IN (''n'', ''m'')
		)
			SELECT w.id, ST_RemoveRepeatedPoints(w.geom) AS geom, ''road'' AS way_type,
				e.class_, e.impedance_surface, e.maxspeed_forward, e.maxspeed_backward,
				w.scenario_id, e.edge_id AS original_id, e.h3_6, e.h3_3
			FROM %s e,
				scenario_features w
			WHERE w.feature_id IS NOT NULL
			AND e.h3_3 = w.h3_3
			AND e.id = w.feature_id
		UNION ALL
			SELECT w.id, ST_RemoveRepeatedPoints(w.geom) AS geom, ''road'' AS way_type,
				''tertiary'' AS class_, NULL AS impedance_surface, 50 AS maxspeed_forward,
				50 AS maxspeed_backward, w.scenario_id, NULL AS original_id, NULL AS h3_6,
				NULL AS h3_3
			FROM scenario_features w
			WHERE w.feature_id IS NULL;
	', scenario_id_input, edge_layer_project_id, edge_network_table);
	CREATE INDEX ON drawn_features USING GIST(geom);

    ---------------------------------------------------------------------------------------------------------------------
	--Snap start and end points
	---------------------------------------------------------------------------------------------------------------------
	/*Round start and end point for snapping*/
	DROP TABLE IF EXISTS snapped_drawn_features; 
 	CREATE TEMP TABLE snapped_drawn_features AS 
 	WITH start_end_point AS 
 	(
		SELECT d.id AS did, st_startpoint(d.geom) geom, 's' AS point_type, FALSE AS snapped, NULL::integer AS node_id 
		FROM drawn_features d
		UNION ALL 
		SELECT d.id AS did, st_endpoint(d.geom) geom, 'e' AS point_type, FALSE AS snapped, NULL AS node_id  
		FROM drawn_features d
	),
	clusters AS 
	(
		SELECT did, geom, ST_ClusterDBSCAN(geom, eps := 0.00001, minpoints := 1) OVER() AS cid, point_type
		FROM start_end_point
	),
	grouped AS 
	(
		SELECT ARRAY_AGG(did) AS did, ST_CENTROID(ST_COLLECT(geom)) AS geom, ARRAY_AGG(point_type)::text[] AS point_types
		FROM clusters 
		GROUP BY cid 
	)
	SELECT UNNEST(did) AS did, geom, UNNEST(point_types) AS point_type, FALSE AS snapped,
		NULL::integer AS node_id, ARRAY_LENGTH(point_types, 1) AS group_size,
		basic.to_short_h3_3(h3_lat_lng_to_cell(geom::point, 3)::bigint) AS h3_3
	FROM grouped;
	
	ALTER TABLE snapped_drawn_features ADD COLUMN id serial; 
	CREATE INDEX ON snapped_drawn_features USING GIST(geom);
	CREATE INDEX ON snapped_drawn_features (id);
	
	/*Snapping to existing Nodes*/
	DROP TABLE IF EXISTS snapped_to_node; 
	EXECUTE FORMAT('
		CREATE TEMP TABLE snapped_to_node AS
		SELECT r.id, r.did, r.point_type, r.geom original_geom,
			s.geom node_geom, s.node_id, s.h3_3
		FROM snapped_drawn_features r
		CROSS JOIN LATERAL 
		(
			SELECT n.node_id, n.geom, n.h3_3
			FROM %s n
			WHERE ST_Intersects(ST_BUFFER(r.geom,0.00001), n.geom)
			ORDER BY r.geom <-> n.geom
			LIMIT 1
		) s;
		CREATE INDEX ON snapped_to_node USING GIST(node_geom);

		UPDATE snapped_drawn_features d
		SET geom = node_geom, snapped = TRUE, node_id = s.node_id, h3_3 = s.h3_3
		FROM snapped_to_node s 
		WHERE s.did = d.did 
		AND d.point_type = s.point_type;
	', node_network_table);
		
	/*Snapping to existing edges*/
	DROP TABLE IF EXISTS snapped_to_edge;
	EXECUTE FORMAT('
		CREATE TEMP TABLE snapped_to_edge AS
		WITH closest_points AS (
			SELECT 
				r.id, r.did, r.point_type, r.geom AS original_geom, ST_CLOSESTPOINT(n.geom, r.geom) AS closest_point_edge,
				basic.to_short_h3_3(h3_lat_lng_to_cell(ST_CLOSESTPOINT(n.geom, r.geom)::point, 3)::bigint) AS h3_3,
				ROW_NUMBER() OVER (PARTITION BY r.geom ORDER BY r.geom <-> ST_CLOSESTPOINT(n.geom, r.geom)) AS rnk
			FROM snapped_drawn_features r
			JOIN %s n
			ON n.h3_3 = r.h3_3
			WHERE ST_Intersects(ST_BUFFER(r.geom, 0.00001), n.geom)
			AND r.snapped = False
		)
		SELECT id, did, point_type, original_geom, closest_point_edge, h3_3
		FROM closest_points
		WHERE rnk = 1;
	', edge_network_table);
	
	/*Update based on snapped to new*/
	UPDATE snapped_drawn_features d
	SET geom = closest_point_edge, snapped = True, h3_3 = s.h3_3
	FROM snapped_to_edge s 
	WHERE s.did = d.did 
	AND d.point_type = s.point_type;
	
	/*Snapping to each other*/
	DROP TABLE IF EXISTS snapped_to_each_other; 
	CREATE TEMP TABLE snapped_to_each_other AS  
	SELECT r.id, r.did, r.point_type, r.geom original_geom, s.geom closest_point_edge 
	FROM snapped_drawn_features r
	CROSS JOIN LATERAL 
	(
		SELECT n.id, ST_CLOSESTPOINT(n.geom, r.geom) AS geom 
		FROM drawn_features n
		WHERE ST_Intersects(ST_BUFFER(r.geom,0.00001), n.geom)
		AND r.did <> n.id 
		ORDER BY r.geom <-> ST_CLOSESTPOINT(n.geom, r.geom)
		LIMIT 1
	) s
	WHERE r.snapped = FALSE
	AND r.group_size = 1
	UNION ALL 
	SELECT s.id, s.did, s.point_type, s.geom, s.geom
	FROM snapped_drawn_features s
	WHERE s.group_size > 1;

	/*Update based on snapped to each other*/
	UPDATE snapped_drawn_features d
	SET geom = closest_point_edge, snapped = True
	FROM snapped_to_each_other s 
	WHERE s.did = d.did 
	AND d.point_type = s.point_type;

	/*Update drawn features*/
	UPDATE drawn_features d
	SET geom = st_setpoint(d.geom, 0, s.geom)
	FROM snapped_drawn_features s
	WHERE d.id = s.did 
	AND s.snapped = TRUE 
	AND s.point_type = 's';
	
	UPDATE drawn_features d
	SET geom = st_setpoint(d.geom, -1, s.geom)
	FROM snapped_drawn_features s
	WHERE d.id = s.did 
	AND s.snapped = TRUE 
	AND s.point_type = 'e';

	UPDATE drawn_features d
	SET geom = st_setpoint(d.geom, 0, s.geom)
	FROM snapped_drawn_features s
	WHERE s.snapped = FALSE 
	AND s.point_type = 's'
	AND d.id = s.did; 
	
	UPDATE drawn_features d
	SET geom = st_setpoint(d.geom, -1, s.geom)
	FROM snapped_drawn_features s
	WHERE s.snapped = FALSE 
	AND s.point_type = 'e'
	AND d.id = s.did;

    ---------------------------------------------------------------------------------------------------------------------
	--Cut network
	---------------------------------------------------------------------------------------------------------------------

	/*Extend lines to cut network*/		
	DROP TABLE IF EXISTS extended_lines; 
	CREATE TEMP TABLE extended_lines AS  
	WITH agg_snapped_nodes AS 
	(
		SELECT d.id, ARRAY_AGG(point_type) AS point_type 
		FROM snapped_to_node s, drawn_features d 
		WHERE d.id = s.did 
		GROUP BY d.id
	)
	SELECT CASE WHEN ARRAY['e', 's'] && point_type THEN d.geom
	WHEN ARRAY['s'] = point_type THEN basic.extend_line(d.geom, 0.00001, 'end')
	WHEN ARRAY['e'] = point_type THEN basic.extend_line(d.geom, 0.00001, 'start')
	END AS geom, d.original_id
	FROM agg_snapped_nodes a, drawn_features d
	WHERE a.id = d.id 
	AND (d.way_type = 'road' OR d.way_type IS NULL)
	UNION ALL 
	SELECT basic.extend_line(d.geom, 0.00001, 'both'), d.original_id  
	FROM drawn_features d 
	LEFT JOIN snapped_to_node s 
	ON d.id = s.did 
	WHERE s.id IS NULL
	AND (d.way_type = 'road' OR d.way_type IS NULL);
	
	/*Intersects drawn bridges*/
	DROP TABLE IF EXISTS start_end_bridges;
	CREATE TEMP TABLE start_end_bridges AS 
	SELECT st_startpoint(geom) AS geom,
		basic.to_short_h3_3(h3_lat_lng_to_cell(st_startpoint(geom)::point, 3)::bigint) AS h3_3
	FROM drawn_features
	WHERE way_type = 'bridge'
	UNION 
	SELECT ST_endpoint(geom) AS geom,
		basic.to_short_h3_3(h3_lat_lng_to_cell(st_endpoint(geom)::point, 3)::bigint) AS h3_3
	FROM drawn_features
	WHERE way_type = 'bridge';
	CREATE INDEX ON start_end_bridges USING GIST(geom);

	/*Intersect drawn ways with existing ways*/
	DROP TABLE IF EXISTS intersection_existing_network;
	EXECUTE FORMAT('
		CREATE TEMP TABLE intersection_existing_network AS 
		WITH intersection_result AS 
		(
			SELECT (ST_DUMP(ST_Intersection(d.geom, w.geom))).geom AS geom, w.edge_id AS id
			FROM extended_lines d, %s w 
			WHERE ST_Intersects(ST_BUFFER(d.geom, 0.00001), w.geom)
		)
		SELECT i.* 
		FROM intersection_result i
		LEFT JOIN extended_lines e
		ON i.id = e.original_id
		WHERE e.original_id IS NULL 
		AND st_geometrytype(i.geom) = ''ST_Point'';
	', edge_network_table);

	EXECUTE FORMAT('
		INSERT INTO intersection_existing_network (geom)
		WITH closest_points AS (
			SELECT 
				%L AS scenario_id, 
				ST_CLOSESTPOINT(w.geom, s.geom) AS closest_point, 
				ST_LineLocatePoint(w.geom, s.geom) AS fraction,
				s.geom AS s_geom,
				ROW_NUMBER() OVER (PARTITION BY s.geom ORDER BY ST_CLOSESTPOINT(w.geom, s.geom) <-> s.geom) AS rnk
			FROM start_end_bridges s
			JOIN %s w 
			ON w.h3_3 = s.h3_3
			WHERE ST_Intersects(ST_Buffer(s.geom, 0.00001), w.geom)
		)
		SELECT closest_point
		FROM closest_points
		WHERE rnk = 1
		AND NOT EXISTS (
			SELECT 1
			FROM intersection_existing_network i
			WHERE ST_Intersects(ST_Buffer(closest_points.closest_point, 0.00001), i.geom)
		);
	', scenario_id_input, edge_network_table);
	
	DROP TABLE IF EXISTS distinct_intersection_existing_network; 
	CREATE TABLE distinct_intersection_existing_network AS 
	SELECT DISTINCT geom
	FROM intersection_existing_network i;  
	
	CREATE INDEX ON distinct_intersection_existing_network USING GIST(geom);
	ALTER TABLE distinct_intersection_existing_network ADD COLUMN id serial;
	ALTER TABLE distinct_intersection_existing_network ADD PRIMARY key(id);
	
	/*Filter out snapped start or end point*/
	DELETE FROM intersection_existing_network h
	USING 
	(
		SELECT h.geom 
		FROM snapped_to_node n, distinct_intersection_existing_network h 
		WHERE ST_Intersects(ST_BUFFER(n.node_geom,0.00001), h.geom)
	) d 
	WHERE h.geom = d.geom;

	DROP TABLE IF EXISTS split_drawn_features;
	/*Split network with itself*/
	SELECT count(*) 
	INTO cnt
	FROM drawn_features
	WHERE (way_type IS NULL OR way_type <> 'bridge')
	LIMIT 2;
	
	IF cnt <= 1 THEN
	    CREATE TEMP TABLE split_drawn_features as
	    SELECT id as did, geom, class_, impedance_surface, maxspeed_forward,
			maxspeed_backward, way_type, scenario_id, original_id, h3_6, h3_3 
		FROM drawn_features;
	ELSE 
		CREATE TEMP TABLE split_drawn_features AS
		SELECT id AS did, basic.split_by_drawn_lines(id, geom) AS geom, class_,
			impedance_surface, maxspeed_forward, maxspeed_backward, way_type,
			scenario_id, original_id, h3_6, h3_3
		FROM drawn_features x
		WHERE (way_type IS NULL OR way_type <> 'bridge')
		UNION ALL 
		SELECT id AS did, geom, class_, impedance_surface, maxspeed_forward,
			maxspeed_backward, way_type, scenario_id, original_id, h3_6, h3_3
		FROM drawn_features
		WHERE way_type = 'bridge';
	END IF;
	CREATE INDEX ON split_drawn_features USING GIST(geom);

	/*Create perpendicular lines to split new network*/
	DROP TABLE IF EXISTS perpendicular_split_lines;
	CREATE TEMP TABLE perpendicular_split_lines AS 
	SELECT basic.create_intersection_line(i.geom, 0.000001) AS geom 
	FROM intersection_existing_network i;

	DROP TABLE IF EXISTS union_perpendicular_split_lines; 
	CREATE TEMP TABLE union_perpendicular_split_lines AS 
	SELECT ST_Union(geom) AS geom  
	FROM perpendicular_split_lines p; 
	
	/*Split new network with existing network*/
	DROP TABLE IF EXISTS new_network;
	CREATE TEMP TABLE new_network AS
	SELECT d.did, (dp.geom).geom, class_, impedance_surface, maxspeed_forward,
		maxspeed_backward, way_type, scenario_id, original_id, 'geom' AS edit_type, 
		h3_6, h3_3
	FROM split_drawn_features d, union_perpendicular_split_lines w, 
	LATERAL (SELECT ST_DUMP(ST_CollectionExtract(ST_SPLIT(d.geom,w.geom),2)) AS geom) dp
	WHERE (d.way_type IS NULL OR d.way_type <> 'bridge');
	CREATE INDEX ON new_network USING GIST(geom);

	/*Delete extended part*/
	DELETE FROM new_network
	WHERE st_length(geom) < 0.0000011;

	/*Inject drawn bridges*/
	INSERT INTO new_network(did, geom, way_type, scenario_id, original_id, edit_type) 
	SELECT id, geom, way_type, scenario_id, original_id, 'geom'
	FROM drawn_features 
	WHERE way_type = 'bridge';

	ALTER TABLE new_network ADD COLUMN id serial;
	ALTER TABLE new_network ADD COLUMN source integer;
	ALTER TABLE new_network ADD COLUMN target integer;

	---------------------------------------------------------------------------------------------------------------------
	--Prepare source and target
	---------------------------------------------------------------------------------------------------------------------
	/*Existing network is split using perpendicular lines*/
	DROP TABLE IF EXISTS existing_network;
	EXECUTE FORMAT('
		CREATE TEMP TABLE existing_network as 
		SELECT w.edge_id AS original_id, (dp.geom).geom, w.source, w.target,
			w.class_, w.impedance_slope, w.impedance_slope_reverse, w.impedance_surface,
			w.maxspeed_forward, w.maxspeed_backward, w.h3_6, w.h3_3
		FROM %s w, union_perpendicular_split_lines p, 
		LATERAL (SELECT ST_DUMP(ST_CollectionExtract(ST_SPLIT(w.geom,p.geom),2)) AS geom) dp
		WHERE ST_Intersects(w.geom, p.geom)
		AND w.edge_id NOT IN (SELECT original_id FROM modified_attributes_only);
		ALTER TABLE existing_network ADD COLUMN id serial;
		ALTER TABLE existing_network ADD PRIMARY KEY(id);
		CREATE INDEX ON existing_network USING GIST(geom);
	', edge_network_table);

	/*Assign vertices that where snapped to new features*/
	UPDATE new_network n
	SET SOURCE = s.node_id
	FROM snapped_drawn_features s
	WHERE n.did = s.did 
	AND s.node_id IS NOT NULL 
	AND s.point_type = 's'
	AND ST_ASTEXT(st_startpoint(n.geom)) = ST_ASTEXT(s.geom); 
	
	UPDATE new_network n
	SET target = s.node_id
	FROM snapped_drawn_features s
	WHERE n.did = s.did 
	AND s.node_id IS NOT NULL 
	AND ST_ASTEXT(st_endpoint(n.geom)) = ST_ASTEXT(s.geom); 

	/*Create new vertices*/
	DROP TABLE IF EXISTS loop_vertices;
	CREATE TEMP TABLE loop_vertices AS
	WITH start_end_point AS 
 	(
		SELECT e.id, st_startpoint(geom) geom, 's' AS point_type 
		FROM new_network e 
		WHERE SOURCE IS NULL 
		UNION ALL 
		SELECT e.id, st_endpoint(geom) geom, 'e' AS point_type 
		FROM new_network e 
		WHERE target IS NULL 
	),
	clusters AS 
	(
		SELECT s.id, s.geom, ST_ClusterDBSCAN(geom, eps := 0.000001, minpoints := 1) OVER() AS cid, point_type
		FROM start_end_point s
	),
	grouped AS 
	(
		SELECT ST_CENTROID(ST_COLLECT(geom)) AS geom, ARRAY_AGG(point_type)::text[] AS point_types, ARRAY_AGG(id)::integer[] new_network_ids
		FROM clusters c
		GROUP BY cid 
	)
	SELECT geom, point_types, new_network_ids
	FROM grouped; 

	DROP TABLE IF EXISTS new_vertices;  
	CREATE TEMP TABLE new_vertices 
	(
		node_id integer,
		new_network_ids integer[],
		point_types text[],
		geom geometry
	);
	/*
	DO $$
	DECLARE 
		rec record;
		max_id integer; 
	BEGIN*/
	FOR rec IN SELECT * FROM loop_vertices v
	LOOP
		INSERT INTO new_vertices(node_id, new_network_ids, point_types, geom)
		SELECT max_node_id + max_node_id_increment AS id, rec.new_network_ids,
			rec.point_types, rec.geom;
		max_node_id_increment := max_node_id_increment + 1;		
	END LOOP;
	/*END $$;*/
	CREATE INDEX ON new_vertices USING GIST(geom);
	
	WITH unnest_to_update AS 
	(
		SELECT v.node_id, UNNEST(v.new_network_ids) new_network_id, UNNEST(v.point_types) point_type
		FROM new_vertices v 
	)
	UPDATE new_network n
	SET SOURCE = u.node_id 
	FROM unnest_to_update u
	WHERE n.id = u.new_network_id 
	AND point_type = 's';
	
	WITH unnest_to_update AS 
	(
		SELECT v.node_id, UNNEST(v.new_network_ids) new_network_id, UNNEST(v.point_types) point_type
		FROM new_vertices v 
	)
	UPDATE new_network n  
	SET target = u.node_id 
	FROM unnest_to_update u
	WHERE n.id = u.new_network_id  
	AND point_type = 'e';

	DROP TABLE IF EXISTS new_source_target_existing; 
	CREATE TEMP TABLE new_source_target_existing AS 
	WITH start_and_end AS 
	(
		SELECT e.id, st_startpoint(geom) geom, 's' AS point_type
		FROM existing_network e 
		UNION ALL 
		SELECT e.id,  st_endpoint(geom) geom, 'e' AS point_type  
		FROM existing_network e
	)
	SELECT v.id, point_type, c.node_id, v.geom  
	FROM start_and_end v
	CROSS JOIN LATERAL 
	(
		SELECT n.node_id 
		FROM new_vertices n
		WHERE ST_Intersects(ST_BUFFER(v.geom, 0.00001), n.geom)
		ORDER BY n.geom <-> v.geom 
		LIMIT 1 
	) c;
	
	UPDATE existing_network e
	SET SOURCE = n.node_id 
	FROM new_source_target_existing n 
	WHERE e.id = n.id 
	AND n.point_type = 's';
	
	UPDATE existing_network e
	SET target = n.node_id 
	FROM new_source_target_existing n 
	WHERE e.id = n.id 
	AND n.point_type = 'e';

	----------------------------------------------------------------------------------------------------------------------
	--PRODUCE FINAL LIST OF NETWORK MODIFICATIONS (SIMPLIFIED INTO ADDITIONS AND DELETIONS)
	----------------------------------------------------------------------------------------------------------------------

	-- Edges to be explicitly deleted according to the scenario
	EXECUTE FORMAT('
		INSERT INTO %I (edit_type, id, h3_6, h3_3)
		SELECT ''d'' AS edit_type, e.edge_id AS id, e.h3_6, e.h3_3
		FROM %s e, (
			SELECT sf.*
			FROM customer.scenario_scenario_feature ssf
			INNER JOIN customer.scenario_feature sf ON sf.id = ssf.scenario_feature_id
			WHERE ssf.scenario_id = %L
			AND sf.layer_project_id = %s
			AND sf.edit_type = ''d''
		) w
		WHERE e.h3_3 = w.h3_3
		AND e.id = w.feature_id;
	', network_modifications_table, edge_network_table, scenario_id_input, edge_layer_project_id);

	-- Existing edges to be deleted due to a modified or new edge replacing it
	EXECUTE FORMAT('
		INSERT INTO %I (edit_type, id, h3_6, h3_3)
		SELECT ''d'' AS edit_type, original_id AS id, h3_6, h3_3
		FROM existing_network
		UNION
		SELECT ''d'' AS edit_type, original_id AS id, h3_6, h3_3
		FROM new_network
		WHERE original_id IS NOT NULL;
	', network_modifications_table);

	-- Create temp table to store all new edges before copying them into the final network modifications table
	DROP TABLE IF EXISTS new_edges;
	EXECUTE FORMAT('
		CREATE TEMP TABLE new_edges AS
		SELECT * FROM %I LIMIT 0;
	', network_modifications_table);

	-- Modified edges to be added to the network
	FOR rec IN SELECT e.* 
				FROM existing_network e
				LEFT JOIN new_network n ON e.original_id = n.original_id
				WHERE n.original_id IS NULL
	LOOP
		INSERT INTO new_edges
		SELECT 'n' AS edit_type, max_edge_id + max_edge_id_increment AS id, rec.class_, rec.source, rec.target, 
			ST_Length(rec.geom::geography) AS length_m, ST_Length(ST_Transform(rec.geom, 3857)) AS length_3857, 
			ST_AsGeoJSON(ST_Transform(rec.geom, 3857))::JSONB->'coordinates' AS coordinates_3857, 
			rec.impedance_slope, rec.impedance_slope_reverse, rec.impedance_surface, 
			rec.maxspeed_forward, rec.maxspeed_backward, rec.geom, rec.h3_6, rec.h3_3;
		max_edge_id_increment := max_edge_id_increment + 1;
	END LOOP;

	-- New edges to be added to the network
	-- TODO: Compute slope impedances
	FOR rec IN SELECT * FROM new_network
	LOOP
		INSERT INTO new_edges
		SELECT 'n' as edit_type, max_edge_id + max_edge_id_increment AS id, rec.class_, rec.source, rec.target, 
			ST_Length(rec.geom::geography) AS length_m, ST_Length(ST_Transform(rec.geom, 3857)) AS length_3857, 
			ST_AsGeoJSON(ST_Transform(rec.geom, 3857))::JSONB->'coordinates' AS coordinates_3857, 
			NULL AS impedance_slope, NULL AS impedance_slope_reverse, rec.impedance_surface, 
			rec.maxspeed_forward, rec.maxspeed_backward, rec.geom,
			basic.to_short_h3_6(h3_lat_lng_to_cell(ST_Centroid(rec.geom)::point, 6)::bigint) AS h3_6,
			basic.to_short_h3_3(h3_lat_lng_to_cell(ST_Centroid(rec.geom)::point, 3)::bigint) AS h3_3;
		max_edge_id_increment := max_edge_id_increment + 1;
	END LOOP;

	-- Copy new edges into the final network modifications table
	EXECUTE FORMAT('
		INSERT INTO %I
		SELECT * FROM new_edges;
	', network_modifications_table);

	RETURN network_modifications_table;

END
$function$;
