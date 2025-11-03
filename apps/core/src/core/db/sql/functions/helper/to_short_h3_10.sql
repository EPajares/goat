CREATE OR REPLACE FUNCTION basic.to_short_h3_10(bigint) RETURNS bigint
AS $$ select ($1 & 'x00fffffffffff000'::bit(64)::bigint>>12)::bit(64)::bigint;$$
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;