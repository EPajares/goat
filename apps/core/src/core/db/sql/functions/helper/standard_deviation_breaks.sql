DROP FUNCTION IF EXISTS basic.standard_deviation_breaks; 
CREATE OR REPLACE FUNCTION basic.standard_deviation_breaks(table_name text, column_name text, where_filter TEXT)
RETURNS JSONB
LANGUAGE plpgsql
AS $function$
DECLARE 
    res JSONB;
    min_val FLOAT;
    max_val FLOAT;
   	mean_val FLOAT;
   	stddev_val FLOAT;
BEGIN
    -- Compute the min, max, and standard deviation directly
    EXECUTE format(
        'SELECT MIN(%I), MAX(%I), AVG(%I), STDDEV(%I) FROM %s WHERE %s',
        column_name, column_name, column_name, column_name, table_name, where_filter
    ) INTO min_val, max_val, mean_val, stddev_val;

    -- Build the JSONB object with the computed breaks
    SELECT JSONB_BUILD_OBJECT('mean', mean_val, 'min', min_val, 'max', max_val, 'breaks', 
   		ARRAY[mean_val - stddev_val * 0.5, mean_val + stddev_val * 0.5, mean_val + stddev_val * 1.5, mean_val + stddev_val * 2.5]
   	)
   	INTO res;
    RETURN res;
END;
$function$;

/*
SELECT basic.standard_deviation_breaks('user_data.point_744e4fd1685c495c8b02efebce875359', 'integer_attr1', 'layer_id = ''ac9cdd4f-8712-459b-bfb8-3e4664c48abb''')
*/
