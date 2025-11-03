DROP FUNCTION IF EXISTS basic.to_full_from_short_h3_3;
CREATE FUNCTION basic.to_full_from_short_h3_3(integer) RETURNS bigint
AS $$ select (($1::bigint::bit(64) & 'x000000000000ffff'::bit(64))<<36 | 'x0830000fffffffff'::bit(64))::bigint;$$
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT
PARALLEL SAFE;

-- From https://github.com/igor-suhorukov/openstreetmap_h3
