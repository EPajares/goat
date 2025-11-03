CREATE OR REPLACE FUNCTION basic.to_short_h3_6(bigint) RETURNS integer
AS $$ select ($1 & 'x000fffffff000000'::bit(64)::bigint>>24)::bit(32)::int;$$
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;
