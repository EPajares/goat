CREATE OR REPLACE FUNCTION basic.identify_dominant_mode(route_types text[], flat_dict jsonb)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
    summary jsonb := '{"bus": false, "tram": false, "metro": false, "rail": false, "other": false}';
    route_mode text;
    route_type integer;
BEGIN
    FOR route_type IN SELECT * FROM unnest(route_types)
    LOOP
        route_mode := flat_dict ->> route_type::text;
        summary := jsonb_set(summary, ARRAY[route_mode], to_jsonb(TRUE));
    END LOOP;
    IF (summary->>'rail')::boolean IS TRUE THEN
        RETURN 'rail';
    ELSIF (summary->>'metro')::boolean IS TRUE THEN
        RETURN 'metro';
    ELSIF (summary->>'tram')::boolean IS TRUE THEN
        RETURN 'tram';
    ELSIF (summary->>'bus')::boolean IS TRUE THEN
        RETURN 'bus';
    ELSIF (summary->>'other')::boolean IS TRUE THEN
        RETURN 'other';
    ELSE
    	RETURN 'unknown';
    END IF;
END;
$function$
