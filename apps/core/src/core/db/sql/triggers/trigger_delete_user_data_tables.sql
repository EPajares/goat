CREATE OR REPLACE FUNCTION customer.delete_user_data_tables()
RETURNS TRIGGER AS $$
DECLARE
    table_name_input text;
    table_exists boolean;
    table_type text;
    user_data_schema text := 'user_data'; -- Declare the schema as a variable
BEGIN
    -- Loop through the table types to drop the tables
    FOR table_type IN (SELECT unnest(ARRAY['point', 'line', 'polygon', 'no_geometry'])) LOOP
        table_name_input := format('%s_%s', table_type, REPLACE(OLD.id::text, '-', ''));

        -- Check if the table exists
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = user_data_schema
            AND table_name = table_name_input
        ) INTO table_exists;

        IF table_exists THEN
            -- Drop the table
            EXECUTE format('DROP TABLE IF EXISTS %I.%I;', user_data_schema, table_name_input);
        END IF;
    END LOOP;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER delete_user_data_tables_trigger
BEFORE DELETE ON accounts.user
FOR EACH ROW
EXECUTE FUNCTION customer.delete_user_data_tables();