DROP FUNCTION IF EXISTS basic.get_h3_neighbors;
CREATE OR REPLACE FUNCTION basic.get_h3_neighbors(h3_3_input integer)
 RETURNS Integer[]
 LANGUAGE plpgsql
AS $function$
DECLARE 
	h3_3_arr Integer[]; 
BEGIN 
	SELECT ARRAY_AGG(z.h3_3)
	INTO h3_3_arr
	FROM (
		SELECT basic.to_short_h3_3(h3_grid_ring_unsafe(to_full_from_short_h3_3(h3_3_input::integer)::h3index)::bigint) AS h3_3
		UNION ALL
		SELECT h3_3_input
	) z;
	RETURN h3_3_arr;
END ;
$function$
PARALLEL SAFE;