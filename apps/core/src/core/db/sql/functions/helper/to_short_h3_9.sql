CREATE OR REPLACE FUNCTION basic.to_short_h3_9(bigint) RETURNS bigint
AS $$ select ($1 & 'x00ffffffffff0000'::bit(64)::bigint>>16)::bit(64)::bigint;$$
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;