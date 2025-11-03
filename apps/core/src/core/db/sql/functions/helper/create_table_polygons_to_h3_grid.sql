DROP FUNCTION IF EXISTS basic.create_table_polygons_to_h3_grid; 
CREATE OR REPLACE FUNCTION basic.create_table_polygons_to_h3_grid(
    input_table text, relevant_columns text, where_filter text,
    result_table_name text, append_existing boolean
)
RETURNS SETOF void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF NOT append_existing THEN
        -- Create empty distributed table 
        EXECUTE format(
            'DROP TABLE IF EXISTS %s;
            CREATE TABLE %s AS SELECT %s, NULL::h3index AS h3_index, NULL::INTEGER AS h3_3
            FROM %s LIMIT 0;',
            result_table_name, result_table_name, relevant_columns, input_table
        );	
        -- Make table distributed
        PERFORM create_distributed_table(result_table_name, 'h3_3');
    END IF;

    -- Assign h3 grid id to the points.
    EXECUTE format(
        'INSERT INTO %s 
        SELECT input_table.%s, h3_index, basic.to_short_h3_3(h3_lat_lng_to_cell(ST_Centroid(h3_boundary)::point, 3)::bigint) AS h3_3
        FROM (SELECT * FROM %s %s) input_table,
        LATERAL basic.fill_polygon_h3_10(input_table.geom);', result_table_name, relevant_columns, input_table, where_filter 
    );

    IF NOT append_existing THEN
        -- Add index 
        EXECUTE format('CREATE INDEX ON %s (h3_index, h3_3);', result_table_name);
    END IF;

END;
$function$ 
PARALLEL SAFE;
