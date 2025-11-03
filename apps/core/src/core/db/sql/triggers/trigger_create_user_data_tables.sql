CREATE OR REPLACE FUNCTION customer.create_user_data_tables()
RETURNS TRIGGER AS $$
DECLARE
    table_name_input text;
    table_exists boolean;
    geom_column text;
    additional_columns text;
    base_columns text;
    table_type text;
    user_data_schema text := 'user_data'; -- Declare the schema as a variable
    query TEXT;

    -- JSON-like structure for column patterns and their respective data types
    column_definitions json := json_build_object(
        'integer', json_build_object('column_name', 'integer_attr', 'data_type', 'INTEGER', 'count', 25),
        'bigint', json_build_object('column_name', 'bigint_attr', 'data_type', 'BIGINT', 'count', 5),
        'float', json_build_object('column_name', 'float_attr', 'data_type', 'FLOAT', 'count', 25),
        'text', json_build_object('column_name', 'text_attr', 'data_type', 'TEXT', 'count', 25),
        'timestamp', json_build_object('column_name', 'timestamp_attr', 'data_type', 'TIMESTAMP', 'count', 3),
        'arrfloat', json_build_object('column_name', 'arrfloat_attr', 'data_type', 'FLOAT[]', 'count', 3),
        'arrint', json_build_object('column_name', 'arrint_attr', 'data_type', 'INTEGER[]', 'count', 3),
        'arrtext', json_build_object('column_name', 'arrtext_attr', 'data_type', 'TEXT[]', 'count', 3),
        'jsonb', json_build_object('column_name', 'jsonb_attr', 'data_type', 'JSONB', 'count', 10),
        'boolean', json_build_object('column_name', 'boolean_attr', 'data_type', 'BOOLEAN', 'count', 10)
    );
    
    key text;
    column_name text;
    column_type text;
    column_count int;
BEGIN
    -- Loop through the table types using an array of values
    FOR table_type IN (SELECT unnest(ARRAY['point', 'line', 'polygon', 'no_geometry'])) LOOP --, 
        table_name_input := format('%s_%s', table_type, REPLACE(NEW.id::text, '-', ''));

        -- Check if the table exists
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = user_data_schema
            AND table_name = table_name_input
        ) INTO table_exists;

        IF NOT table_exists THEN
            -- Build base columns by iterating through the JSON structure
            base_columns := '';
            
            -- Loop through the JSON keys to generate columns
            FOR key IN SELECT * FROM json_object_keys(column_definitions) LOOP
                column_name := column_definitions->key->>'column_name';
                column_type := column_definitions->key->>'data_type';
                column_count := (column_definitions->key->>'count')::int;
                
                -- Append columns based on the JSON data
                FOR i IN 1..column_count LOOP
                    base_columns := base_columns || format('%I%s %s, ', column_name, i, column_type);
                END LOOP;
            END LOOP;

            -- Handle geometry column and additional columns
            IF table_type = 'no_geometry' THEN
                geom_column := '';
                additional_columns := '';
                base_columns := rtrim(base_columns, ', ');
            ELSE
                geom_column := 'geom GEOMETRY,';

                IF table_type = 'street_network_line' THEN
                    additional_columns := ' source integer NOT NULL, target integer NOT NULL, h3_3 integer NULL, h3_6 integer NOT NULL';
                ELSIF table_type = 'street_network_point' THEN
                    additional_columns := ' connector_id integer NOT NULL, h3_3 integer NULL, h3_6 integer NOT NULL';
                ELSE
                    additional_columns := ' cluster_keep boolean, h3_3 integer NULL, h3_group h3index NULL';
                END IF;
            END IF;

            -- Create the table query
            EXECUTE format('
                CREATE TABLE %I.%I (
                    id UUID DEFAULT basic.uuid_generate_v7() NOT NULL,
                    layer_id UUID NOT NULL,
					%s
                    %s
                    %s,
                    updated_at timestamptz NOT NULL DEFAULT to_char((CURRENT_TIMESTAMP AT TIME ZONE ''UTC''), ''YYYY-MM-DD"T"HH24:MI:SSOF'')::timestamp with time zone,
        			created_at timestamptz NOT NULL DEFAULT to_char((CURRENT_TIMESTAMP AT TIME ZONE ''UTC''), ''YYYY-MM-DD"T"HH24:MI:SSOF'')::timestamp with time zone,
                    PRIMARY KEY(id)
                );', 
                user_data_schema, table_name_input, geom_column, base_columns, additional_columns
            );
           
		   	IF table_type IN ('point', 'line', 'polygon') THEN
				EXECUTE format('
				    CREATE TRIGGER trigger_%I
				    BEFORE INSERT OR UPDATE ON %I.%I
				    FOR EACH ROW EXECUTE FUNCTION basic.set_user_data_h3();', 
				    table_name_input, user_data_schema, table_name_input
				);
				
				EXECUTE format('CREATE INDEX ON %I.%I USING GIST(layer_id, geom);', 
				    user_data_schema, table_name_input
				);
			
				EXECUTE format('CREATE INDEX ON %I.%I (layer_id, h3_group);', 
				    user_data_schema, table_name_input
				);
				
				EXECUTE format('CREATE INDEX ON %I.%I (layer_id, cluster_keep);', 
				    user_data_schema, table_name_input
				);
				
			END IF;
            
        END IF;
    END LOOP;
   
   	-- Create home folder
	INSERT INTO customer.folder(user_id, name, updated_at)
	SELECT NEW.id, 'home', now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_user_data_tables_trigger
AFTER INSERT ON accounts.user
FOR EACH ROW
EXECUTE FUNCTION customer.create_user_data_tables();