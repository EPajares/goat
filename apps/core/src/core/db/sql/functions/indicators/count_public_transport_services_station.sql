DROP FUNCTION IF EXISTS basic.count_public_transport_services_station;
CREATE OR REPLACE FUNCTION basic.count_public_transport_services_station(
	table_area TEXT,
	area_layer_project_id INT,
	customer_schema TEXT,
	scenario_id TEXT,
	where_filter TEXT,
	start_time interval,
	end_time interval,
	weekday integer
)
RETURNS TABLE(stop_id text, stop_name text, parent_station text, trip_cnt jsonb, geom geometry, trip_ids jsonb, h3_3 integer)
LANGUAGE plpgsql
AS $function$
DECLARE
	temp_table_stops TEXT := 'temporal.' || '"' || REPLACE(uuid_generate_v4()::TEXT, '-', '') || '"';
	temp_table_area TEXT := 'temporal.' || '"' || REPLACE(uuid_generate_v4()::TEXT, '-', '') || '"'; 
BEGIN

	-- Build table reference area
	PERFORM basic.create_distributed_polygon_table
	(
		table_area,
		area_layer_project_id,
		'',
		customer_schema,
		scenario_id,
		where_filter,
		30, 
		temp_table_area
	); 
	
	-- Create temporary table and execute dynamic SQL
	EXECUTE format(
		'DROP TABLE IF EXISTS %s;
		CREATE TABLE %s
		(
			stop_id TEXT,
			h3_3 integer
		);', temp_table_stops, temp_table_stops
	);
	-- Distribute the table with stops
	PERFORM create_distributed_table(temp_table_stops, 'h3_3');

	-- Get relevant stations
	EXECUTE format(
		'INSERT INTO %s
		SELECT st.stop_id, st.h3_3
		FROM basic.stops st, %s b
		WHERE ST_Intersects(st.geom, b.geom)
		AND (st.location_type IS NULL OR st.location_type = ''0'')
		AND st.h3_3 = b.h3_3',
		temp_table_stops, temp_table_area
	);

	-- Count trips per station and transport mode in respective time interval
	RETURN QUERY EXECUTE format(
		'WITH trip_cnt AS
		(
			SELECT c.stop_id, j.route_type, cnt AS cnt, j.trip_ids, c.h3_3
			FROM %s c
			CROSS JOIN LATERAL (
				SELECT t.route_type, SUM(weekdays[$1]::integer) cnt, ARRAY_AGG(trip_id) AS trip_ids
				FROM basic.stop_times_optimized t, basic.stops s
				WHERE t.stop_id = s.stop_id
				AND s.stop_id = c.stop_id
				AND s.h3_3 = c.h3_3
				AND t.h3_3 = s.h3_3
				AND t.arrival_time BETWEEN $2 AND $3
				AND weekdays[$4] = True
				GROUP BY t.route_type
			) j
		),
		o AS (
			SELECT stop_id, jsonb_object_agg(route_type, cnt) AS trip_cnt, jsonb_object_agg(route_type, g.trip_ids) AS trip_ids, h3_3
			FROM trip_cnt g
			WHERE cnt <> 0
			GROUP BY stop_id, h3_3
		)
		SELECT s.stop_id, s.stop_name, s.parent_station, o.trip_cnt, s.geom, o.trip_ids, o.h3_3
		FROM o, basic.stops s
		WHERE o.stop_id = s.stop_id
		AND s.h3_3 = o.h3_3', temp_table_stops) USING weekday, start_time, end_time, weekday;

	-- Drop the temporary table
	EXECUTE format(
		'DROP TABLE IF EXISTS %s; DROP TABLE IF EXISTS %s;',
		temp_table_stops, temp_table_area
	);
END;
$function$
PARALLEL SAFE;
/*
SELECT *
FROM basic.count_public_transport_services_station('06:00','20:00', 1, 'SELECT geom
FROM user_data.polygon_744e4fd1685c495c8b02efebce875359') s
*/