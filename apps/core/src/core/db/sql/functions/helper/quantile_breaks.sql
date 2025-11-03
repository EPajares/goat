DROP FUNCTION IF EXISTS basic.quantile_breaks;
CREATE OR REPLACE FUNCTION basic.quantile_breaks(table_name text, column_name text, where_filter TEXT, breaks integer)
RETURNS JSONB
LANGUAGE plpgsql
AS $function$
DECLARE 
	computed_breaks float[];
    min_val FLOAT;
    max_val FLOAT;
   	mean_val FLOAT; 
    res JSONB;
BEGIN
    -- Compute quantile borders, min and max
    EXECUTE format(
        'SELECT AVG(%I), MIN(%I), MAX(%I), percentile_disc(Array(SELECT generate_series(1, %L) / %L::numeric))
		WITHIN GROUP (ORDER BY %I ASC) AS borders
		FROM %s
		WHERE %s',
        column_name, column_name, column_name, breaks + 1, breaks + 1, column_name, table_name, where_filter
    ) INTO mean_val, min_val, max_val, computed_breaks;
	
   	-- Build the JSONB object with the computed breaks. Remove the last element as it is the same as max_val.
   	res = jsonb_build_object('mean', mean_val, 'min', min_val, 'max', max_val, 'breaks', computed_breaks[1:array_length(computed_breaks, 1) - 1]);
    RETURN res;
END;
$function$
PARALLEL SAFE;

/*
SELECT basic.quantile_breaks('user_data.point_744e4fd1685c495c8b02efebce875359', 'integer_attr1', 'layer_id = ''ac9cdd4f-8712-459b-bfb8-3e4664c48abb''', 5)
*/
