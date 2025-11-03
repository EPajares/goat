CREATE OR REPLACE FUNCTION basic.create_intersection_line(point_geom geometry, length_line double precision)
 RETURNS SETOF geometry
 LANGUAGE sql
 IMMUTABLE
AS $function$
	SELECT ST_SETSRID(ST_MAKELINE(
		ST_Translate(point_geom, length_line, length_line),
		ST_Translate(point_geom, -length_line, -length_line)
	), 4326)
$function$;
