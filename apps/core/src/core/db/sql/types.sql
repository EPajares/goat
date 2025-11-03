DROP TYPE IF EXISTS type_fetch_edges_routing CASCADE;
CREATE TYPE type_fetch_edges_routing AS
(
	id integer, 
	SOURCE integer, 
	target integer,
	length_3857 float, 
	cost float,
	reverse_cost float,
	death_end integer,
	coordinates_3857 json,
	starting_ids integer[],
	starting_geoms text[] 
);