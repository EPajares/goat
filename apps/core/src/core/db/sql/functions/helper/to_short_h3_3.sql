DROP FUNCTION IF EXISTS basic.to_short_h3_3;
CREATE OR REPLACE FUNCTION basic.to_short_h3_3(bigint) RETURNS integer
AS $$ select ($1 & 'x000ffff000000000'::bit(64)::bigint>>36)::int;$$
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;

-- From https://github.com/igor-suhorukov/openstreetmap_h3
