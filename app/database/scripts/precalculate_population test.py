import psycopg2
import time
import math
from variables_precalculate import *
from db_functions import ReadYAML
from db_functions import DB_connection
import yaml

#Step defined the bulk size of the heatmap calculation
step = 200

start = time.time()

db_name,user,host,port,password = ReadYAML().db_credentials()
db = DB_connection(db_name,user,host,port,password)

con,cursor = db.con_psycopg()


sql_ordered_pois = '''
DROP TABLE IF EXISTS compute_sections_2; 
CREATE TABLE compute_sections_2 AS
WITH b AS 
(
	SELECT ST_BUFFER(geom::geography, 1600)::geometry AS geom 
	FROM study_area_union 
),
g AS 
(
	SELECT (ST_DUMP(makegrid_2d(ST_BUFFER(geom::geography, 1600)::geometry, 2000, 2000))).geom
	FROM b
)
SELECT ROW_NUMBER() OVER() AS section_id, g.geom 
FROM b, g
WHERE ST_Intersects(b.geom,g.geom);

CREATE INDEX ON compute_sections_2 USING GIST(geom);

DROP TABLE IF EXISTS pois_ordered;
CREATE TABLE pois_ordered AS 
SELECT starting_points, centroid, geom, gid, section_id, ROW_NUMBER() over() AS id 
FROM (
    SELECT ARRAY[ST_X(p.geom)::numeric,ST_Y(p.geom)::numeric] starting_points, p.geom, p.gid, c.section_id 
    FROM pois p, reached_pois_heatmap g, compute_sections c 
    WHERE ST_Intersects(p.geom,c.geom) AND p.gid = g.gid
    ORDER BY section_id
) x;
ALTER TABLE pois_ordered ADD PRIMARY key(gid);
CREATE INDEX ON pois_ordered USING GIST(centroid);'''

cursor.execute(sql_ordered_pois)
con.commit()

sql_edges_pois = '''
DROP TABLE IF EXISTS reached_edges_pois;
CREATE TABLE reached_edges_pois 
(
	id serial, 
	edge bigint,
	gids integer[],
	amenity text [],
	name text[],
	start_cost smallint[],
	end_cost smallint[],
	userid integer,
	scenario_id integer,
	geom geometry,
	start_perc float,
	end_perc float,
	partial_edge boolean,
	CONSTRAINT reached_edges_pois_pkey PRIMARY KEY (id)
);

CREATE INDEX ON reached_edges_pois (userid);
CREATE INDEX ON reached_edges_pois (edge);
CREATE INDEX ON reached_edges_pois (scenario_id);
CREATE INDEX ON reached_edges_pois USING gist(geom);

CREATE INDEX ON reached_edges_pois USING gin (gids gin__int_ops);

DROP TABLE IF EXISTS reached_population_pois;
CREATE TABLE reached_population_pois (
	id serial,
	gid integer,
	amenity text,
	name text,
	gids_pop integer[],
	population float[],
	arr_cost integer[],
	edge integer,
	fraction float,
	accessibility_indices integer[],
	userid integer,
	scenario_id integer,
	CONSTRAINT reached_population_pois_pkey PRIMARY KEY (id)
);
ALTER TABLE reached_population_pois ADD CONSTRAINT 
reached_population_pois_gid_fkey FOREIGN KEY(gid)
REFERENCES pois_userinput(gid)
ON DELETE CASCADE; 

CREATE INDEX ON reached_population_pois USING gin (gids_pop gin__int_ops);
CREATE INDEX ON reached_population_pois USING gin (arr_cost gin__int_ops);
CREATE INDEX ON reached_population_pois (edge);
CREATE INDEX ON reached_population_pois (gid);
CREATE INDEX ON reached_population_pois (amenity);
'''
print('Bulk calculation is starting...')
cursor.execute(sql_edges_pois)

cursor.execute('SELECT array_agg(section_id) FROM (SELECT DISTINCT section_id FROM pois_ordered ORDER BY section_id) x;')
section_ids = cursor.fetchall()[0][0]

sql_bulk_calculation = '''WITH x AS 
(
	SELECT array_agg(starting_points) AS array_starting_points, array_agg(gid) AS gids
	FROM pois_ordered 
	WHERE section_id = %i
)
SELECT pgrouting_edges_heatmap(ARRAY[1200.], x.array_starting_points, 1.33, x.gids, 1, 'walking_standard',0,0,%i)
FROM x;
'''

#Loop for routing calculation
for i in section_ids:
	print('Compute routing section: %s' % str(i))
	cursor.execute(sql_bulk_calculation % (i, i))
	con.commit()

time_routing = time.time()-start
print('Routing calculation has finished after: %s s' % (time_routing))


#Loop for closest POIs calculation (needs to be executed after routing is completed)
for i in section_ids: 
	print('Compute reached population section: %s' % str(i))
	cursor.execute('''SELECT reached_population_pois(geom,0.0014,'default',0) 
	FROM compute_sections 
	WHERE section_id = %s
	''' % str(i))
	con.commit()

print('Closest POIs calculation has finished after: %s s' % (time.time()-start-time_routing))

#Compute Accessibility Values
cursor.execute('SELECT compute_accessibility(0)')
con.commit()
#Loop for isochrone area calculation
cursor.execute('SELECT gid FROM reached_pois_heatmap;')
gridids = cursor.fetchall()

for i in gids:
	i = i[0]
	cursor.execute(f'''SELECT compute_area_isochrone({i},0,1,0);''')	
	con.commit()

cursor.execute(sql_grid_population)

con.commit()
con.close()
end = time.time()
print('Running the script took:')
print(end - start)