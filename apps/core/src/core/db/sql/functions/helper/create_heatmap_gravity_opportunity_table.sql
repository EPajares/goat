DROP FUNCTION IF EXISTS basic.create_heatmap_gravity_opportunity_table;
CREATE OR REPLACE FUNCTION basic.create_heatmap_gravity_opportunity_table(
    input_layer_project_id int, input_table text, customer_schema text, scenario_id text,
    geofence_table text, geofence_where_filter text, geofence_buffer_dist float,
    max_traveltime int, sensitivity float, potential_column text, where_filter text,
    result_table_name text, grid_resolution int, is_area_based boolean,
    filler_cells_table_name text, append_existing boolean
)
RETURNS SETOF void
LANGUAGE plpgsql
AS $function$
DECLARE
    temp_opportunities_table TEXT;
    base_query TEXT;
    filler_cells_query TEXT;
    geofence_query TEXT;
    hexagon_dia NUMERIC = h3_get_hexagon_edge_length_avg(grid_resolution, 'm') * 2;
BEGIN
    IF NOT append_existing THEN
        -- Create empty distributed table 
        EXECUTE format(
            'DROP TABLE IF EXISTS %s;
            CREATE TABLE %s (
                id UUID,
                h3_index h3index,
                max_traveltime smallint,
                sensitivity float,
                potential float,
                h3_3 int
            );',
            result_table_name, result_table_name
        );	
        -- Make table distributed
        PERFORM create_distributed_table(result_table_name, 'h3_3');

        -- Create filler cells table if opportunities are area-based
        IF filler_cells_table_name IS NOT NULL THEN
            EXECUTE format(
                'DROP TABLE IF EXISTS %s;
                CREATE TABLE %s (
                    h3_index h3index,
                    max_traveltime smallint,
                    sensitivity float,
                    potential float
                );',
                filler_cells_table_name, filler_cells_table_name
            );
        END IF;
    END IF;

    -- Ensure grid resolution is supported
    IF grid_resolution NOT IN (10, 9, 8) THEN
		RAISE EXCEPTION 'Unsupported grid resolution specified';
	END IF;

    -- Create a temporary table containing opportunities after applying scenarios
    SELECT 'temporal.opportunities_' || basic.uuid_generate_v7() INTO temp_opportunities_table;
    EXECUTE format(
        '
            CREATE TABLE %I AS
            WITH scenario_features AS (
                SELECT sf.feature_id AS id, sf.geom, sf.edit_type, %s AS potential
                FROM %s.scenario_scenario_feature ssf
                INNER JOIN %s.scenario_feature sf ON sf.id = ssf.scenario_feature_id
                WHERE ssf.scenario_id = %L
                AND sf.layer_project_id = %s
            )
                SELECT of.id, geom, %s AS potential
                FROM (SELECT * FROM %s WHERE %s) of
                LEFT JOIN (SELECT id FROM scenario_features) sf ON of.id = sf.id
                WHERE sf.id IS NULL
            UNION ALL
                SELECT id, geom, potential
                FROM scenario_features
                WHERE edit_type IN (''n'', ''m'');
        ',
        temp_opportunities_table, potential_column, customer_schema, customer_schema,
        scenario_id, input_layer_project_id, potential_column, input_table, where_filter
    );

    -- Produce h3 grid at specified resolution
    IF NOT is_area_based THEN
        base_query := format(
            'INSERT INTO %s
            SELECT
                id,
                h3_lat_lng_to_cell(input_features.geom::point, %s) AS h3_index,
                %s AS max_traveltime,
                %s AS sensitivity,
                potential,
                basic.to_short_h3_3(h3_lat_lng_to_cell(input_features.geom::point, 3)::bigint) AS h3_3
            FROM (
                SELECT *
                FROM %I
            ) input_features',
            result_table_name, grid_resolution, max_traveltime, sensitivity,
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
                %s AS sensitivity,
                potential,
                basic.to_short_h3_3(h3_lat_lng_to_cell(input_features.geom::point, 3)::bigint) AS h3_3
            FROM (
                SELECT id, (dump).geom, potential
                FROM (
                    SELECT id, ST_DumpPoints(
                            CASE
                                WHEN ST_Length(geom::geography) > %s
                                THEN ST_LineInterpolatePoints(geom, (%s / ST_Length(geom::geography)))
                                ELSE geom
                            END
                        ) AS dump, potential
                    FROM (
                        SELECT id, (ST_Dump(ST_Boundary(geom))).geom as geom, potential
                        FROM %I
                    ) lines
                ) points
            ) input_features',
            result_table_name, grid_resolution, grid_resolution, max_traveltime,
            sensitivity, hexagon_dia, hexagon_dia, temp_opportunities_table
        );

        -- Produce filled H3 grid for area-based opportunities
        filler_cells_query := format(
            'INSERT INTO %s
            SELECT
                filled.h3index,
                %s AS max_traveltime,
                %s AS sensitivity,
                potential
            FROM %I input_features,
            LATERAL basic.fill_polygon_h3(geom, %s) filled',
            filler_cells_table_name, max_traveltime, sensitivity, temp_opportunities_table,
            grid_resolution
        );
    END IF;

    -- Append geofence check if required
    IF geofence_table IS NOT NULL THEN
        -- Build geofence query
        geofence_query := format(
            ', (SELECT ST_Buffer(ST_Union(geom)::geography, %s) AS geom FROM %s WHERE %s) geofence
            WHERE input_features.geom && geofence.geom
            AND ST_Intersects(input_features.geom, geofence.geom)',
            geofence_buffer_dist, geofence_table, geofence_where_filter
        );

        -- Append geofence check for main query
        base_query := base_query || geofence_query;

        -- Append geofence check for filler cells query if required
        IF is_area_based THEN
            filler_cells_query := filler_cells_query || geofence_query;
        END IF;
    END IF;

    -- Execute the final query
    EXECUTE base_query;

    -- Execute the filler cells query if required
    IF is_area_based THEN
        EXECUTE filler_cells_query;
    END IF;

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
