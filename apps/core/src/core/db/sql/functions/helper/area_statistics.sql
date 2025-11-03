DROP FUNCTION IF EXISTS basic.area_statistics; 
CREATE OR REPLACE FUNCTION basic.area_statistics(operation text, table_name text, where_filter TEXT)
RETURNS JSONB
LANGUAGE plpgsql
AS $function$
DECLARE 
    result JSONB;
   	pg_operation TEXT; 
BEGIN

    pg_operation = CASE operation
        WHEN 'mean' THEN 'AVG'
        ELSE operation
    END;

    EXECUTE format(
        'SELECT JSONB_BUILD_OBJECT(''%s'', %s(ST_Area(geom::geography))) FROM %s %s',
        operation, pg_operation, table_name, where_filter
    ) INTO result;

    RETURN result;
END;
$function$ 
PARALLEL SAFE;
/*
SELECT *
FROM basic.area_statistics('sum', 'user_data.polygon_744e4fd1685c495c8b02efebce875359', 'layer_id = ''4bdbed8f-4804-4913-9b42-c547e7be0fd5''')
*/