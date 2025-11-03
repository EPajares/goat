DROP FUNCTION IF EXISTS basic.create_distributed_line_table; 
CREATE OR REPLACE FUNCTION basic.create_distributed_line_table(
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
		CREATE TABLE %s AS 
		SELECT id AS feature_id, geom, NULL::INTEGER AS h3_3 %s
        FROM %s
        LIMIT 0;
        ALTER TABLE %s ADD COLUMN id INTEGER;
        CREATE SEQUENCE %s_id_seq;
        ALTER TABLE %s ALTER COLUMN id SET DEFAULT nextval(''%s_id_seq'');
        ALTER SEQUENCE %s_id_seq OWNED BY %s.id;',
        result_table_name, result_table_name, relevant_columns, input_table,
        result_table_name, result_table_name, result_table_name, result_table_name,
        result_table_name, result_table_name
    );
    -- Make table distributed
   PERFORM create_distributed_table(result_table_name, 'h3_3'); 
   
   	-- Insert feature that are within one h3_3 grid 
   EXECUTE format(
        'INSERT INTO %s
        SELECT id AS feature_id, l.geom, h.h3_3 %s
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
        ) l, basic.h3_grid_resolution_3 h
        WHERE ST_Intersects(l.geom, h.geom)
        AND ST_WITHIN(l.geom, h.geom);',
        result_table_name, relevant_columns, relevant_columns, customer_schema,
        customer_schema, scenario_id, input_layer_project_id, relevant_columns,
        input_table, where_filter, relevant_columns
   ); 

    -- Insert all where the lines intersect the border of the h3 grid and clip them using intersection.
    EXECUTE format(
        'INSERT INTO %s 
        SELECT id AS feature_id, ST_Intersection(l.geom, h.geom) AS geom, h.h3_3 %s
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
        ) l, basic.h3_grid_resolution_3 h
        WHERE ST_Intersects(l.geom, h.geom)
        AND ST_Intersects(l.geom, ST_ExteriorRing(h.geom));',
        result_table_name, relevant_columns, relevant_columns, customer_schema,
        customer_schema, scenario_id, input_layer_project_id, relevant_columns,
        input_table, where_filter, relevant_columns
    ); 
	
   -- Add indices
   	EXECUTE format('ALTER TABLE %s ADD PRIMARY KEY (h3_3, id);', result_table_name);
   	EXECUTE format('CREATE INDEX ON %s USING GIST(h3_3, geom);', result_table_name);

END;
$function$ 
PARALLEL SAFE;

/*
SELECT basic.create_distributed_line_table(
'test_user_data.line_744e4fd1685c495c8b02efebce875359', 'text_attr1', 'WHERE text_attr1 = ''Im Anspann''', 
'temporal.test_lines')
*/