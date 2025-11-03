CREATE OR REPLACE FUNCTION basic.to_short_h3_8(bigint) RETURNS bigint
AS $$ select ($1 & 'x00fffffffff00000'::bit(64)::bigint>>20)::bit(64)::bigint;$$
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;
