CREATE OR REPLACE FUNCTION basic.extend_line(geom geometry, extend_distance NUMERIC, point_to_extend text)
RETURNS geometry 
LANGUAGE plpgsql
AS $function$
DECLARE
	start_geom geometry; 
	end_geom geometry;
	azimuth_A float;
	azimuth_B float;
	length_A NUMERIC;
	length_B NUMERIC;
	newpoint_A geometry;
	newpoint_B geometry;
	new_line geometry; 
BEGIN 
		
	-- get the points A and B given a line L
	start_geom = ST_STARTPOINT(geom);
	end_geom = ST_ENDPOINT(geom);
		
	-- Start line section
	azimuth_A = ST_AZIMUTH(ST_POINTN(geom,2),start_geom);

	-- End line section 
	azimuth_B = ST_AZIMUTH(ST_POINTN(geom,-2),end_geom);
	
	-- get the length of the line A --> B
	length_A = ST_DISTANCE(ST_STARTPOINT(geom),ST_POINTN(geom,2));
	length_B = ST_DISTANCE(ST_ENDPOINT(geom),ST_POINTN(geom,-2));
	
	newpoint_A = ST_TRANSLATE(start_geom, sin(azimuth_A) * extend_distance, cos(azimuth_A) * extend_distance);
	newpoint_B = ST_TRANSLATE(end_geom, sin(azimuth_B) * extend_distance, cos(azimuth_B) * extend_distance);
	
	IF point_to_extend = 'start' THEN
		new_line = st_addpoint(geom, newpoint_a, 0);
	ELSEIF point_to_extend = 'end' THEN 
		new_line = st_addpoint(geom, newpoint_b, -1);
	ELSEIF point_to_extend = 'both' THEN 
		new_line = st_addpoint(st_addpoint(geom,newpoint_B), newpoint_A, 0);
	ELSE 
		RAISE EXCEPTION 'Please specify a valid point_to_extend type.';
	END IF; 

	If new_line IS NULL THEN 
		RAISE NOTICE 'The new line is NULL. Please check the input parameters.';
		new_line = geom;
	END IF; 

	RETURN new_line;
END
$function$
/*point_to_extend = 'start', 'end', 'both'*/
--1 meter in Germany approx. 0.0000127048
--SELECT basic.extend_line(geom, 0.0127048, 'both') 
--FROM customer.way_modified WHERE id = 112;
