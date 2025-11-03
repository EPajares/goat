DROP FUNCTION IF EXISTS basic.heads_and_tails_breaks;
CREATE OR REPLACE FUNCTION basic.heads_and_tails_breaks(table_name text, column_name text, where_filter TEXT, breaks INT)
RETURNS JSONB AS $$
DECLARE 
    arr_mean float;
    reply float[] := ARRAY[]::float[];
    min_val float;
    max_val float;
   	mean_val float; 
    i INT := 1;
    result JSONB;
    current_break float;
BEGIN 
    -- Compute min and max values
    EXECUTE format('SELECT AVG(%I::float), MIN(%I::float), MAX(%I::float) FROM %s WHERE %s', 
                   column_name, column_name, column_name, table_name, where_filter) 
                   INTO mean_val, min_val, max_val;

	current_break = mean_val;
    -- Append initial break
    reply := array_append(reply, current_break);

    -- Iteratively calculate the average of elements greater than the last average
    WHILE i < breaks LOOP
        EXECUTE format('SELECT AVG(%I::float) FROM %s WHERE %I::float > %s AND %s', 
                       column_name, table_name, column_name, current_break, where_filter)
                       INTO current_break;

        -- Break loop if no more distinct values
        IF current_break IS NULL THEN
	        WHILE i < breaks LOOP
	            reply := array_append(reply, max_val);
	            i := i + 1;
	        END LOOP;
	        EXIT;
	    END IF;
	   
        -- Append the break and increment
        reply := array_append(reply, current_break);
        i := i + 1;
    END LOOP;

    result := jsonb_build_object('mean', mean_val, 'min', min_val, 'max', max_val, 'breaks', reply);
    RETURN result;
END;
$$ LANGUAGE plpgsql
PARALLEL SAFE;

-- Inspired from https://github.com/CartoDB/cartodb-postgresql/blob/master/scripts-available/CDB_HeadsTailsBins.sql

/*
DROP TABLE temporal.test;
CREATE TABLE temporal.test AS 
SELECT generate_series(1, 1000000) AS d;   
SELECT basic.heads_and_tails_breaks('temporal.test', 'd', 'd > 1', 5)
*/
