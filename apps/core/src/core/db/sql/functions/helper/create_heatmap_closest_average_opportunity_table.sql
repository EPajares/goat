DROP FUNCTION IF EXISTS basic.create_heatmap_closest_average_opportunity_table; 
CREATE OR REPLACE FUNCTION basic.create_heatmap_closest_average_opportunity_table(
    input_layer_project_id int, input_table text, customer_schema text, scenario_id text,
    geofence_table text, geofence_where_filter text, geofence_buffer_dist float,
    max_traveltime int, num_destinations int, where_filter text, result_table_name text,
    grid_resolution int, is_area_based boolean, append_existing boolean
)
RETURNS SETOF void
LANGUAGE plpgsql
AS $function$
DECLARE
    temp_opportunities_table TEXT;
    base_query TEXT;
BEGIN
    IF NOT append_existing THEN
        -- Create empty distributed table 
        EXECUTE format(
            'DROP TABLE IF EXISTS %s;
            CREATE TABLE %s (
                id UUID,
                h3_index h3index,
                max_traveltime smallint,
                num_destinations int,
                h3_3 int
            );',
            result_table_name, result_table_name
        );	
        -- Make table distributed
        PERFORM create_distributed_table(result_table_name, 'h3_3');
    END IF;

    -- Ensure grid resolution is supported
    IF grid_resolution NOT IN (10, 9, 8) THEN
		RAISE EXCEPTION 'Unsupported grid resolution specified';
	END IF;

    -- Create a temporary table containing opportunities after applying scenarios
    SELECT 'temporal.opportunities_' || basic.uuid_generate_v7() INTO temp_opportunities_table;
    EXECUTE format(
        '
            CREATE TEMPORARY TABLE %I AS
            WITH scenario_features AS (
                SELECT sf.feature_id AS id, sf.geom, sf.edit_type
                FROM %s.scenario_scenario_feature ssf
                INNER JOIN %s.scenario_feature sf ON sf.id = ssf.scenario_feature_id
                WHERE ssf.scenario_id = %L
                AND sf.layer_project_id = %s
            )
                SELECT original_features.id, original_features.geom
                FROM (SELECT id, geom FROM %s WHERE %s) original_features
                LEFT JOIN scenario_features ON original_features.id = scenario_features.id
                WHERE scenario_features.id IS NULL
            UNION ALL
                SELECT scenario_features.id, scenario_features.geom
                FROM scenario_features
                WHERE edit_type IN (''n'', ''m'');
        ',
        temp_opportunities_table, customer_schema, customer_schema, scenario_id,
        input_layer_project_id, input_table, where_filter
    );

    -- Produce h3 grid at specified resolution
    IF NOT is_area_based THEN
        base_query := format(
            'INSERT INTO %s
            SELECT 
                id,
                h3_lat_lng_to_cell(input_features.geom::point, %s) AS h3_index,
                %s AS max_traveltime,
                %s AS num_destinations,
                basic.to_short_h3_3(h3_lat_lng_to_cell(input_features.geom::point, 3)::bigint) AS h3_3
            FROM (
                SELECT *
                FROM %I
            ) input_features',
            result_table_name, grid_resolution, max_traveltime, num_destinations,
            temp_opportunities_table
        );
    ELSE
        base_query := format(
            'INSERT INTO %s
            SELECT
                DISTINCT ON (id, h3_lat_lng_to_cell(input_features.geom::point, %s))
                id,
                h3_lat_lng_to_cell(input_features.geom::point, %s) AS h3_index,
                %s AS max_traveltime,
                %s AS num_destinations,
                basic.to_short_h3_3(h3_lat_lng_to_cell(input_features.geom::point, 3)::bigint) AS h3_3
            FROM (
                SELECT id, (ST_DumpPoints(ST_Boundary(geom))).geom AS geom
                FROM %I
            ) input_features',
            result_table_name, grid_resolution, grid_resolution, max_traveltime,
            num_destinations, temp_opportunities_table
        );
    END IF;

    -- Append geofence check if required
    IF geofence_table IS NOT NULL THEN
        base_query := base_query || format(
            ', (SELECT ST_Buffer(ST_Union(geom)::geography, %s) AS geom FROM %s WHERE %s) geofence
            WHERE input_features.geom && geofence.geom
            AND ST_Intersects(input_features.geom, geofence.geom)',
            geofence_buffer_dist, geofence_table, geofence_where_filter
        );
    END IF;

    -- Execute the final query
    EXECUTE base_query;

    IF NOT append_existing THEN
        -- Add index 
        EXECUTE format('CREATE INDEX ON %s (h3_index, h3_3);', result_table_name);
    END IF;

    -- Cleanup
    EXECUTE format(
        'DROP TABLE IF EXISTS %I;',
        temp_opportunities_table
    );

END;
$function$ 
PARALLEL SAFE;
