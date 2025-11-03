CREATE FUNCTION basic.summarize_trip_count(trip_cnt jsonb, flat_dict jsonb) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    summary jsonb := '{"bus": 0, "tram": 0, "metro": 0, "rail": 0, "other": 0}';
    key text;
    value integer := 0;
    category text;
    pair jsonb;
BEGIN
    FOR pair IN SELECT * FROM jsonb_each_text(trip_cnt)
    LOOP
 
        key := flat_dict ->> pair::text;
        value := (trip_cnt ->> pair::text)::integer;
        summary := jsonb_set(summary, ARRAY[key], to_jsonb(((summary->>key)::integer + value)::text));
    END LOOP;
    RETURN summary;
END;
$$;
