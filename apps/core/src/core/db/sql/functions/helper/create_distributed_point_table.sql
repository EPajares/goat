DROP FUNCTION IF EXISTS basic.create_distributed_point_table; 
CREATE OR REPLACE FUNCTION basic.create_distributed_point_table(
    input_table text, input_layer_project_id int, relevant_columns text, customer_schema text,
    scenario_id text, where_filter text, result_table_name text
)
RETURNS SETOF void
LANGUAGE plpgsql
AS $function$
BEGIN
    -- Create empty distributed table 
    EXECUTE format(
        'DROP TABLE IF EXISTS %s;
        CREATE TABLE %s AS SELECT id, geom, NULL::INTEGER AS h3_3 %s
        FROM %s
        LIMIT 0;',
        result_table_name, result_table_name, relevant_columns, input_table
    );
    -- Make table distributed
    PERFORM create_distributed_table(result_table_name, 'h3_3'); 

    -- Assign h3 grid id to the points.
    EXECUTE format(
        'INSERT INTO %s 
        SELECT id, geom, basic.to_short_h3_3(h3_lat_lng_to_cell(geom::point, 3)::bigint) AS h3_3 %s
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
        result_table_name, relevant_columns, relevant_columns, customer_schema,
        customer_schema, scenario_id, input_layer_project_id, relevant_columns,
        input_table, where_filter, relevant_columns
    ); 

    -- Add GIST index 
    EXECUTE format('CREATE INDEX ON %s USING GIST(h3_3, geom)', result_table_name);

END;
$function$ 
PARALLEL SAFE;