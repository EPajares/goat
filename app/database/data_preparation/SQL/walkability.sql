
----##########################################################################################################################----
----########################################################SIDEWALK QUALITY##################################################----
----##########################################################################################################################----
--prepara data
UPDATE footpath_visualization f 
SET sidewalk = 'yes' 
WHERE sidewalk IS NULL 
AND highway in ('footway', 'path', 'cycleway', 'living_street', 'steps', 'pedestrian', 'track');

UPDATE footpath_visualization f 
SET surface = 'asphalt' 
WHERE surface IS NULL 
AND highway IN ('residential','tertiary','secondary','secondary_link','primary','primary_link','living_street');

UPDATE footpath_visualization f 
SET surface = NULL 
WHERE surface NOT IN ('paved','asphalt','concrete','concrete:lanes','paving_stones','cobblestone:flattened','stone','sandstone','sett','metal','unhewn_cobblestone','cobblestone','unpaved','compacted','fine_gravel','metal_grid','gravel','pebblestone','rock','wood','ground','dirt','earth','grass','grass_paver','mud','sand');

UPDATE footpath_visualization f
SET incline_percent = slope 
FROM slope_profile_footpath_visualization s 
WHERE ST_EQUALS(f.geom, s.geom);

UPDATE footpath_visualization 
SET surface = 'unpaved' 
WHERE highway = 'track' 
AND surface IS NULL; 

-- Slope is computed using a digital elevation model in a python function
UPDATE footpath_visualization 
SET incline_percent = 0 
WHERE incline_percent IS NULL
OR length_m < 0.5; 

--calculate score
UPDATE footpath_visualization f SET sidewalk_quality = 
round(group_index(
	ARRAY[
		select_weight_walkability('sidewalk',
			(CASE WHEN lower(sidewalk) IN ('no','none') THEN 'no' 
			WHEN lower(sidewalk) = 'yes' THEN 'yes'
			ELSE NULL END)
		), 
		select_weight_walkability('surface',surface),
		select_weight_walkability_range('incline_percent', incline_percent::numeric),
		COALESCE(select_weight_walkability('highway',highway),100 * (SELECT DISTINCT weight FROM walkability w WHERE "attribute" = 'highway'))
	],
	ARRAY[
		select_full_weight_walkability('sidewalk'),
		select_full_weight_walkability('surface'),
		select_full_weight_walkability('incline_percent'),
		select_full_weight_walkability('highway')
	]
),0);

----##########################################################################################################################----
----#######################################################TRAFFIC PROTECTION#################################################----
----##########################################################################################################################----
--prepara data
DROP TABLE IF EXISTS lanes_buffer;
CREATE TABLE lanes_buffer as
SELECT ST_SUBDIVIDE(ST_BUFFER(w.geom,0.00015), 50) AS geom, lanes
FROM ways w, study_area s 
WHERE highway IN ('living_street','residential','secondary','secondary_link','tertiary','tertiary_link','primary','primary_link','trunk','motorway')
AND ST_Intersects(w.geom,s.geom)
AND lanes IS NOT NULL; 

CREATE INDEX ON lanes_buffer USING GIST(geom);

DROP TABLE IF EXISTS maxspeed_buffer;
CREATE TEMP TABLE maxspeed_buffer as
SELECT ST_SUBDIVIDE(ST_BUFFER(w.geom,0.00015), 50) AS geom, maxspeed_forward AS maxspeed
FROM ways w, study_area s 
WHERE highway IN ('living_street','residential','secondary','secondary_link','tertiary','tertiary_link','primary','primary_link','trunk','motorway')
AND ST_Intersects(w.geom,s.geom)
AND maxspeed_forward IS NOT NULL; 

CREATE INDEX ON maxspeed_buffer USING GIST(geom);

UPDATE footpath_visualization 
SET lanes = 0 
WHERE highway IN ('footway','pedestrian','steps','cycleway');

UPDATE footpath_visualization 
SET lanes = 1 
WHERE highway IN ('track','path');

DROP TABLE IF EXISTS footpath_lanes;
CREATE TEMP TABLE footpath_lanes AS 
SELECT id, MAX(COALESCE(arr_polygon_attr[array_position(arr_shares, array_greatest(arr_shares))]::integer, 0)) AS lanes
FROM footpaths_get_polygon_attr('lanes_buffer','lanes')
GROUP BY id ;
ALTER TABLE footpath_lanes ADD PRIMARY KEY(id); 

DROP TABLE IF EXISTS footpath_maxspeed;
CREATE TABLE footpath_maxspeed AS 
SELECT id, MAX(COALESCE(arr_polygon_attr[array_position(arr_shares, array_greatest(arr_shares))]::integer, 0)) AS maxspeed
FROM footpaths_get_polygon_attr('maxspeed_buffer','maxspeed')
GROUP BY id; 			
ALTER TABLE footpath_maxspeed ADD PRIMARY KEY(id);


DO $$
	DECLARE 
    	buffer float := meter_degree() * 15;
    BEGIN 
	    WITH footpaths_parking AS 
	    (
			SELECT f.id 
			FROM footpath_visualization f, landuse_osm l 
			WHERE ST_Intersects(l.geom, f.geom)
			AND l.landuse = 'parking'
		)
		UPDATE footpath_visualization f 
		SET parking = 'off_street'
		FROM footpaths_parking p 
		WHERE f.id = p.id; 
	END; 
$$;


/*
DO $$
	DECLARE 
    	buffer float := meter_degree() * 10;
    BEGIN 
	    DROP TABLE buffer_parking; 
	    CREATE TABLE buffer_parking AS 
	    SELECT ST_BUFFER(geom, buffer) AS geom, 'on_street' AS parking 
		FROM parking 
		WHERE parking_lane NOT IN ('no','no_parking','no_stopping')
		OR parking_lane IS NULL; 
		
	
	END; 
$$;

SELECT count(parking_lane), parking_lane 
FROM parking 
GROUP BY parking_lane 

UPDATE footpath_visualization 

WITH footpaths_no_parking AS 
(
	SELECT DISTINCT id 
	FROM ways_cleaned w, 
	LATERAL (
		SELECT DISTINCT parking 
		FROM 
		(
			SELECT w.parking 
			UNION ALL 
			SELECT w.parking_lane_left
			UNION ALL 
			SELECT w.parking_lane_right
			UNION ALL 
			SELECT w.parking_lane_both
		) x
		WHERE parking IN ('no_stopping','no_parking','no')
	) p
)
UPDATE footpath_visualization f  
SET parking = 'no'
FROM footpaths_no_parking n 
WHERE f.id = n.id;

SELECT * 
FROM footpaths 
WHERE highway IN ('secondary','tertiary','residential','living_street','service','unclassified')



SELECT * FROM test 
*/

UPDATE footpath_visualization 
SET parking = 'no' 
WHERE parking IS NULL;

UPDATE footpath_visualization f
SET lanes = l.lanes 
FROM footpath_lanes l
WHERE f.id = l.id; 

UPDATE footpath_visualization 
SET lanes = 2
WHERE highway = 'residential' AND lanes = 0;

UPDATE footpath_visualization f
SET maxspeed = m.maxspeed 
FROM footpath_maxspeed m
WHERE f.id = m.id;

--street crossings
-- Create temp table to count street crossings
DROP TABLE IF EXISTS relevant_crossings;
CREATE TEMP TABLE relevant_crossings AS 
SELECT geom 
FROM street_crossings 
WHERE crossing IN ('zebra','traffic_signals'); 

CREATE INDEX ON relevant_crossings USING GIST(geom);

/*Assing number of crossing to footpath_visualization*/
ALTER TABLE footpath_visualization DROP COLUMN IF EXISTS cnt_crossings;
ALTER TABLE footpath_visualization ADD COLUMN cnt_crossings int; 
WITH cnt_table AS 
(
	SELECT id, COALESCE(points_sum) AS points_sum 
	FROM footpaths_get_points_sum('relevant_crossings', 30)
)
UPDATE footpath_visualization f
SET cnt_crossings = points_sum 
FROM cnt_table c
WHERE f.id = c.id;

/*Label footpaths that are not affected by crossings*/
UPDATE footpath_visualization 
SET cnt_crossings = -1
WHERE maxspeed <= 30 
OR maxspeed IS NULL OR highway IN ('residential','service');
 

/*For each footpath noise levels (day and night) are derived an aggregated for different sound sources*/
DO $$     
	DECLARE 
		noise_key TEXT;
    BEGIN     

		IF EXISTS ( 	
			SELECT 1
            FROM   information_schema.tables 
            WHERE  table_schema = 'public'
            AND    table_name = 'noise'
        ) 
		THEN 
		
			DROP TABLE IF EXISTS noise_levels_footpaths;
			CREATE TEMP TABLE noise_levels_footpaths 
			(
				gid serial, 
				footpath_id integer, 
				noise_level_db integer, 
				noise_type text,
			CONSTRAINT noise_levels_footpaths_pkey PRIMARY KEY (gid)
			);

			FOR noise_key IN SELECT DISTINCT noise_type FROM noise  	
			LOOP
				RAISE NOTICE 'Following noise type will be calculated: %', noise_key;
				DROP TABLE IF EXISTS noise_subdivide;
				CREATE TEMP TABLE noise_subdivide AS 
				SELECT ST_SUBDIVIDE((ST_DUMP(geom)).geom, 50) AS geom, noise_level_db  
				FROM noise fn 
				WHERE noise_type = noise_key;
				
				ALTER TABLE noise_subdivide ADD COLUMN gid serial;
				ALTER TABLE noise_subdivide ADD PRIMARY KEY(gid);
				CREATE INDEX ON noise_subdivide USING GIST(geom);
				
				INSERT INTO noise_levels_footpaths(footpath_id,noise_level_db,noise_type)
				SELECT id, 
				COALESCE(arr_polygon_attr[array_position(arr_shares, array_greatest(arr_shares))]::integer, 0) AS val, noise_key
				FROM footpaths_get_polygon_attr('noise_subdivide','noise_level_db');
				
			END LOOP;
		END IF; 
    END
$$ ;

WITH noise_day AS 
(
	SELECT footpath_id, ROUND((10 * LOG(SUM(power(10,(noise_level_db::numeric/10))))),2) AS noise 
	FROM noise_levels_footpaths
	WHERE noise_type LIKE '%day%'
	GROUP BY footpath_id
)
UPDATE footpath_visualization f
SET noise_day = n.noise 
FROM noise_day n  
WHERE f.id = n.footpath_id; 

WITH noise_night AS 
(
	SELECT footpath_id, ROUND((10 * LOG(SUM(power(10,(noise_level_db::numeric/10))))),2) AS noise 
	FROM noise_levels_footpaths
	WHERE noise_type LIKE '%night%'
	GROUP BY footpath_id
)
UPDATE footpath_visualization f
SET noise_night = n.noise 
FROM noise_night n  
WHERE f.id = n.footpath_id; 

/*Count Accidents*/
/*Assing number of crossing to footpath_visualization*/
DROP TABLE IF EXISTS accidents_foot; 
CREATE TABLE accidents_foot AS 
SELECT geom 
FROM accidents 
WHERE istfuss = '1'; 

CREATE INDEX ON accidents_foot USING GIST(geom);

WITH cnt_table AS 
(
	SELECT f.id, COALESCE(points_sum,0) AS points_sum 
	FROM footpath_visualization f 
	LEFT JOIN footpaths_get_points_sum('accidents_foot', 30) c
	ON f.id = c.id 	
)
UPDATE footpath_visualization f
SET cnt_accidents = points_sum 
FROM cnt_table c
WHERE f.id = c.id;

--Aggregated score
UPDATE footpath_visualization f SET traffic_protection = 
round(group_index(
	ARRAY[
		select_weight_walkability_range('lanes',lanes),
		select_weight_walkability_range('maxspeed',maxspeed),
		select_weight_walkability_range('crossings',cnt_crossings),
		select_weight_walkability_range('accidents',cnt_accidents),
		select_weight_walkability_range('noise',noise_day::numeric),
		select_weight_walkability('parking',parking)
	],
	ARRAY[
		select_full_weight_walkability('lanes'),
		select_full_weight_walkability('maxspeed'),
		select_full_weight_walkability('crossings'),
		select_full_weight_walkability('accidents'),
		select_full_weight_walkability('noise'),
		select_full_weight_walkability('parking')
	]
),0);

UPDATE footpath_visualization SET traffic_protection = 100
WHERE traffic_protection IS NULL; 

UPDATE footpath_visualization 
SET traffic_protection = (traffic_protection - 30) / 0.7;

UPDATE footpath_visualization 
SET traffic_protection = 0
WHERE traffic_protection < 0;

----##########################################################################################################################----
----#####################################################SECURITY#############################################################----
----##########################################################################################################################----

--Underpasses
UPDATE footpath_visualization f 
SET covered = p.covered
FROM planet_osm_line p
WHERE f.osm_id = p.osm_id;

UPDATE footpath_visualization f 
SET covered = p.tunnel
FROM planet_osm_line p
WHERE f.osm_id = p.osm_id
AND p.tunnel IS NOT NULL;

UPDATE footpath_visualization f 
SET covered = 'no'
WHERE covered IS NULL;

--Illuminance
WITH variables AS 
(
    SELECT select_from_variable_container_o('lit') AS lit
)
UPDATE footpath_visualization f SET lit_classified = x.lit_classified
FROM
    (SELECT f.id,
    CASE WHEN 
        lit IN ('yes','Yes','automatic','24/7','sunset-sunrise') 
        OR (lit IS NULL AND highway IN (SELECT jsonb_array_elements_text((lit ->> 'highway_yes')::jsonb) FROM variables)
			AND maxspeed<80)
        THEN 'yes' 
    WHEN
        lit IN ('no','No','disused')
        OR (lit IS NULL AND (highway IN (SELECT jsonb_array_elements_text((lit ->> 'highway_no')::jsonb) FROM variables) 
        OR surface IN (SELECT jsonb_array_elements_text((lit ->> 'surface_no')::jsonb) FROM variables)
		OR maxspeed>=80)
        )
        THEN 'no'
    ELSE 'unclassified'
    END AS lit_classified 
    FROM footpath_visualization f
    ) x
WHERE f.id = x.id;

--Precalculation of visualized features for lit
DROP TABLE IF EXISTS buffer_lamps;
CREATE TABLE buffer_lamps as
SELECT ST_SUBDIVIDE((ST_DUMP(ST_UNION(ST_BUFFER(geom,15 * meter_degree())))).geom, 100) AS geom, 'yes' AS lit 
FROM street_furniture
WHERE amenity = 'street_lamp';

CREATE INDEX ON buffer_lamps USING gist(geom);

DROP TABLE IF EXISTS footpaths_lit; 
CREATE TEMP TABLE footpaths_lit AS 
SELECT DISTINCT id 
FROM footpaths_get_polygon_attr('buffer_lamps','lit')
WHERE arr_shares IS NOT NULL 
AND arr_polygon_attr = ARRAY['yes']
AND arr_shares[1] > 0.3; 

UPDATE footpath_visualization f  
SET lit_classified = 'yes'
FROM footpaths_lit l 
WHERE f.id = l.id;

UPDATE footpath_visualization f SET security = 
round(group_index(
	ARRAY[
		select_weight_walkability('lit_classified',lit_classified),
		select_weight_walkability('covered',covered)
	],
	ARRAY[
		select_full_weight_walkability('lit_classified'),
		select_full_weight_walkability('covered')
	]
),0);

----##########################################################################################################################----
----#####################################################GREEN & BLUE#############################################################----
----##########################################################################################################################----

DROP TABLE IF EXISTS green_ndvi_vec; 
CREATE TABLE green_ndvi_vec AS 
SELECT (ST_DUMPASPOLYGONS(rast)).geom, (ST_DUMPASPOLYGONS(rast)).val  
FROM green_ndvi;

ALTER TABLE green_ndvi_vec ADD COLUMN gid serial; 
ALTER TABLE green_ndvi_vec ADD PRIMARY KEY(gid);
CREATE INDEX ON green_ndvi_vec USING GIST(geom);

DO $$
	DECLARE 
    	buffer float := meter_degree() * 15;
    BEGIN 

		DROP TABLE IF EXISTS footpaths_green_ndvi;
		CREATE TEMP TABLE footpaths_green_ndvi AS  
		SELECT f.id, 
		CASE WHEN j.avg_green_ndvi < 0 THEN 0::integer ELSE COALESCE((j.avg_green_ndvi * 100)::integer,0) END AS avg_green_ndvi
		FROM footpath_visualization f
		CROSS JOIN LATERAL 
		(
			SELECT AVG(val) AS avg_green_ndvi
			FROM green_ndvi_vec g
			WHERE ST_DWITHIN(f.geom, g.geom, buffer)
		) j;

		ALTER TABLE footpaths_green_ndvi ADD PRIMARY KEY(id);
	END; 
$$;

UPDATE footpath_visualization f 
SET vegetation = g.avg_green_ndvi 
FROM footpaths_green_ndvi g
WHERE f.id = g.id;

/*Coputing rank for water. These queries still don't scale for larger study areas.*/
DROP TABLE IF EXISTS buffer_water_large;
CREATE TABLE buffer_water_large as
SELECT ST_SUBDIVIDE(ST_UNION(ST_BUFFER(way::geography, 50)::geometry), 50) AS geom, 'water' AS water 
FROM planet_osm_polygon 
WHERE (water IS NOT NULL 
OR ("natural" = 'water' AND water IS NULL))
AND ST_AREA(way::geography) > 30000
AND (water <> 'wastewater' OR water IS NULL);

CREATE INDEX ON buffer_water_large USING gist(geom);

DROP TABLE IF EXISTS buffer_water_small;
CREATE TABLE buffer_water_small AS
SELECT ST_SUBDIVIDE(ST_UNION(geom), 50) AS geom, 'water' AS water
FROM 
(
	SELECT ST_UNION(ST_BUFFER(way::geography, 25)::geometry) AS geom 
	FROM planet_osm_polygon 
	WHERE (water IS NOT NULL 
	OR ("natural" = 'water' AND water IS NULL))
	AND ST_AREA(way::geography) < 30000
	AND (water <> 'wastewater' OR water IS NULL)
	UNION ALL 
	SELECT ST_UNION(ST_BUFFER(way::geography, 25)::geometry) AS geom 
	FROM planet_osm_line 
	WHERE waterway IS NOT NULL
) w;

CREATE INDEX ON buffer_water_small USING gist(geom);

DROP TABLE IF EXISTS water_rank;
CREATE TABLE water_rank AS 
SELECT id, arr_shares[1] * 100 AS water_rank 
FROM footpaths_get_polygon_attr('buffer_water_large','water')
WHERE arr_polygon_attr IS NOT NULL; 

INSERT INTO water_rank 
SELECT id, arr_shares[1] * 50 AS water_rank 
FROM footpaths_get_polygon_attr('buffer_water_small','water')
WHERE arr_polygon_attr IS NOT NULL; 

WITH grouped_rank AS 
(
	SELECT id, CASE WHEN SUM(water_rank) > 100 THEN 100 ELSE sum(water_rank) END AS water_rank  
	FROM water_rank 
	GROUP BY id 
)
UPDATE footpath_visualization f
SET water = g.water_rank 
FROM grouped_rank g
WHERE g.id = f.id; 

UPDATE footpath_visualization 
SET green_blue_index = COALESCE(water,0) + (CASE WHEN vegetation > 75 THEN 100 ELSE vegetation END);

UPDATE footpath_visualization 
SET green_blue_index = 100 
WHERE green_blue_index > 100;

----##########################################################################################################################----
----#####################################################WALKING ENVIRONMENT##################################################----
----##########################################################################################################################----

--Classify by number of POIs
CREATE TEMP TABLE pois_to_count AS 
SELECT geom 
FROM pois 
WHERE amenity NOT IN ('parking','bench','information','parking_space','waste_basket','fountain','toilets','carging_station','bicycle_parking','parking_entrance','motorcycle_parking','hunting_stand');

CREATE INDEX ON pois_to_count USING GIST(geom);

WITH cnt_table AS 
(
	SELECT f.id, COALESCE(points_sum,0) AS points_sum, f.geom  
	FROM footpath_visualization f 
	LEFT JOIN footpaths_get_points_sum('pois_to_count', 50) c
	ON f.id = c.id 	
), 
classify AS 
(
	SELECT c.id, sring_condition 
	FROM walkability w, cnt_table c 
	WHERE attribute = 'pois'
	AND (w.min_value <= c.points_sum OR w.min_value IS NULL)  
	AND (w.max_value > c.points_sum OR w.max_value IS NULL)
)
UPDATE footpath_visualization f
SET pois = c.sring_condition 
FROM classify c
WHERE f.id = c.id;

DROP TABLE pois_to_count;

--Classify by number of Population
WITH cnt_table AS 
(
	SELECT id, points_sum
	FROM footpaths_get_points_sum('population', 50, 'population') c
),
percentiles AS 
(
	SELECT id, points_sum, ntile(4) over (order by points_sum) AS percentile
	FROM cnt_table 
	WHERE points_sum <> 0 
	AND points_sum IS NOT NULL 
),
combined AS 
(
	SELECT f.id, (COALESCE(p.percentile,0) + 1) AS arr_index 
	FROM footpath_visualization f 
	LEFT JOIN percentiles p 
	ON f.id = p.id 
)
UPDATE footpath_visualization f
SET population = (ARRAY['no','low','medium','high','very_high'])[arr_index] 
FROM combined c 
WHERE f.id = c.id; 

DO $$
	DECLARE 
    	buffer float := meter_degree() * 50;
    BEGIN 
		
	    DROP TABLE IF EXISTS landuse_arrays; 
	    CREATE TABLE landuse_arrays AS 
	    WITH landuse_footpath AS 
	    (
			SELECT ARRAY_AGG(landuse_simplified) AS landuse, id 
			FROM footpath_visualization f, landuse_osm l
			WHERE ST_DWITHIN(f.geom, l.geom, buffer)
			AND ST_AREA(l.geom::geography) > 500
			GROUP BY id 
		)
		SELECT f.id, ARRAY_AGG(l.landuse) AS landuse 
		FROM landuse_footpath f, 
		LATERAL (SELECT DISTINCT landuse FROM UNNEST(landuse) landuse WHERE landuse IS NOT NULL) l   
		GROUP BY f.id; 
		
		ALTER TABLE landuse_arrays ADD PRIMARY KEY (id);
		UPDATE footpath_visualization f  
		SET landuse = l.landuse 
		FROM landuse_arrays l 
		WHERE f.id = l.id;
		
		DROP TABLE IF EXISTS landuse_penalty; 
		CREATE TABLE landuse_penalty AS 
		SELECT landuse_simplified landuse, ST_SUBDIVIDE(ST_BUFFER(geom, buffer)::geometry, 50) AS geom 
		FROM landuse_osm l 
		WHERE landuse_simplified IN ('commercial','industrial','military')
		AND landuse NOT IN ('retail')
		AND ST_AREA(geom::geography) > 500
		UNION ALL 
		SELECT landuse, ST_SUBDIVIDE(ST_BUFFER(geom, buffer)::geometry, 50) AS geom 
		FROM landuse_additional l 
		WHERE landuse IN('Railways and associated land', 'Airports');		
		CREATE INDEX ON landuse_penalty USING GIST(geom);
	
	END; 
$$;

DROP TABLE IF EXISTS penalty_shares; 
CREATE TABLE penalty_shares AS 
WITH landuse_shares AS 
(
	SELECT *, ARRAY_LENGTH(arr_polygon_attr, 1) AS len_array
	FROM footpaths_get_polygon_attr('landuse_penalty','landuse')
	WHERE arr_polygon_attr IS NOT NULL 
),
landuse_values AS 
(
	SELECT id, AVG(a.shares * w.value)
	FROM landuse_shares s, walkability w, 
	LATERAL (SELECT UNNEST(s.arr_polygon_attr) AS landuse, UNNEST(s.arr_shares) AS shares) a
	WHERE arr_polygon_attr IS NOT NULL
	AND w."attribute" = 'landuse'
	AND w.sring_condition = a.landuse
	GROUP BY id 
),
share_other_landuse AS 
(
	SELECT x.id, CASE 
	WHEN sum(x.shares) = 0 THEN 1
	WHEN sum(x.shares) < 1 THEN (1-sum(x.shares)) 
	ELSE 0 END AS share_other  
	FROM (SELECT id, UNNEST(arr_shares) AS shares FROM landuse_shares l) x  
	GROUP BY id 
)
SELECT v.id, avg + (o.share_other * 100/s.len_array ) AS value
FROM landuse_values v
LEFT JOIN landuse_shares s
ON v.id = s.id
LEFT JOIN share_other_landuse o 
ON v.id = o.id; 

CREATE INDEX ON penalty_shares (id);

WITH landuse_values AS 
(
	SELECT f.id, COALESCE(p.value, 100) * (SELECT DISTINCT weight FROM walkability WHERE ATTRIBUTE = 'landuse') AS value 
	FROM footpath_visualization f
	LEFT JOIN penalty_shares p 
	ON f.id = p.id 	
)
UPDATE footpath_visualization f SET liveliness = 
round(group_index(
	ARRAY[
		l.value::NUMERIC, 
		select_weight_walkability('population',population),
		select_weight_walkability('pois',pois)
	],
	ARRAY[
		select_full_weight_walkability('landuse'),
		select_full_weight_walkability('population'),
		select_full_weight_walkability('pois')
	]
),0)
FROM landuse_values l  
WHERE f.id = l.id;


----##########################################################################################################################----
----###########################################################COMFORT########################################################----
----##########################################################################################################################----

-- Benches
-- Create temp table to count benches
DROP TABLE IF EXISTS benches;
CREATE TEMP TABLE benches AS 	
SELECT geom 
FROM street_furniture 
WHERE amenity = 'bench';
CREATE INDEX ON benches USING GIST(geom);

WITH cnt_table AS 
(
	SELECT f.id, COALESCE(points_sum,0) AS points_sum 
	FROM footpath_visualization f 
	LEFT JOIN footpaths_get_points_sum('benches', 30) c
	ON f.id = c.id 	
)
UPDATE footpath_visualization f
SET cnt_benches = points_sum 
FROM cnt_table c
WHERE f.id = c.id;

--- Waste-baskets
DROP TABLE IF EXISTS waste_baskets;
CREATE TEMP TABLE waste_baskets AS 
SELECT geom 
FROM street_furniture 
WHERE amenity = 'waste_basket';
CREATE INDEX ON waste_baskets USING GIST(geom);

WITH cnt_table AS 
(
	SELECT f.id, COALESCE(points_sum,0) AS points_sum 
	FROM footpath_visualization f 
	LEFT JOIN footpaths_get_points_sum('waste_baskets', 20) c
	ON f.id = c.id 	
)
UPDATE footpath_visualization f
SET cnt_waste_baskets = points_sum 
FROM cnt_table c
WHERE f.id = c.id;

--- Fountains
DROP TABLE IF EXISTS fountains;
CREATE TEMP TABLE fountains AS 
SELECT geom 
FROM street_furniture 
WHERE amenity IN ('fountain','drinking_water');
CREATE INDEX ON fountains USING GIST(geom);

WITH cnt_table AS 
(
	SELECT f.id, COALESCE(points_sum,0) AS points_sum 
	FROM footpath_visualization f 
	LEFT JOIN footpaths_get_points_sum('fountains', 50) c
	ON f.id = c.id 	
)
UPDATE footpath_visualization f
SET cnt_fountains = points_sum 
FROM cnt_table c
WHERE f.id = c.id;

--- Bathrooms
DROP TABLE IF EXISTS toilets;
CREATE TEMP TABLE toilets AS 
SELECT geom 
FROM street_furniture 
WHERE amenity IN ('toilets');
CREATE INDEX ON toilets USING GIST(geom);

WITH cnt_table AS 
(
	SELECT f.id, COALESCE(points_sum,0) AS points_sum 
	FROM footpath_visualization f 
	LEFT JOIN footpaths_get_points_sum('toilets', 300) c
	ON f.id = c.id 	
)
UPDATE footpath_visualization f
SET cnt_toilets = points_sum 
FROM cnt_table c
WHERE f.id = c.id;

--- Street furniture sum
UPDATE footpath_visualization f 
SET comfort = round(10 * (2*cnt_benches + 3*cnt_waste_baskets + 3*cnt_toilets + cnt_fountains),0);

UPDATE footpath_visualization f 
SET comfort = 100 
WHERE comfort > 100;

WITH weighting AS
(
	SELECT id, CASE WHEN comfort IS NULL THEN 0 ELSE 0.07 END AS comfort_weight,
	CASE WHEN green_blue_index IS NULL THEN 0 ELSE 0.14 END AS green_blue_index_weight,
	CASE WHEN security IS NULL THEN 0 ELSE 0.07 END AS security_weight,
	CASE WHEN traffic_protection IS NULL THEN 0 ELSE 0.21 END AS traffic_protection_weight,
	CASE WHEN sidewalk_quality IS NULL THEN 0 ELSE 0.14 END AS sidewalk_quality_weight,
	CASE WHEN liveliness IS NULL THEN 0 ELSE 0.14 END AS liveliness_weight     
	FROM footpath_visualization 
)
UPDATE footpath_visualization f
SET walkability  = 
round(
	((green_blue_index*green_blue_index_weight) + (security*security_weight) 
	+ (traffic_protection*traffic_protection_weight) + (sidewalk_quality*sidewalk_quality_weight) + (liveliness*liveliness_weight))
	/
	(green_blue_index_weight + security_weight + traffic_protection_weight + sidewalk_quality_weight + liveliness_weight)
,0) + COALESCE(comfort,0) * comfort_weight 
FROM weighting w 
WHERE f.id = w.id; 

UPDATE footpath_visualization f 
SET data_quality = (22-num_nulls(sidewalk,incline_percent,surface,highway,lanes,maxspeed,cnt_crossings,parking,
cnt_accidents,noise_day,noise_night,lit_classified,covered,vegetation,water,population,pois,landuse,
cnt_benches,cnt_waste_baskets,cnt_fountains,cnt_toilets))::float/22.0;

UPDATE footpath_visualization 
SET walkability = (walkability - 30) / 0.7;

UPDATE footpath_visualization 
SET walkability = 0 
WHERE walkability < 0;

UPDATE footpath_visualization 
SET walkability = 100 
WHERE walkability > 100;