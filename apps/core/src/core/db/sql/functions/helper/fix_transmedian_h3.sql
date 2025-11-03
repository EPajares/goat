CREATE OR REPLACE FUNCTION basic.fix_transmeridian_h3(h3index h3index) RETURNS geometry AS $$
DECLARE
    geom geometry;
   	new_geom geometry := 'GEOMETRYCOLLECTION EMPTY'::geometry;
   	min_lon float;
   	max_lon float;
   	point geometry;
   	lon float;
    lat float;
    i int;
BEGIN
	--This function is useful to fix h3 grids spanning accross the transmeridian. Without this the polygon would show as long bands.

	geom := h3_cell_to_boundary(h3index)::geometry;
    min_lon := ST_XMin(geom);
    max_lon := ST_XMax(geom);
	
    IF min_lon < -170 AND max_lon > 170 THEN
	    -- Check and handle different geometry types
	    IF ST_GeometryType(geom) = 'ST_Polygon' OR ST_GeometryType(geom) = 'ST_LineString' THEN
	        -- Create an empty geometry of the same type
	        new_geom := ST_SetSRID(ST_Collect(ARRAY[]::geometry[]), ST_SRID(geom));
	        
	        -- Iterate over each point
	        FOR i IN 1..ST_NPoints(geom) LOOP
	            point := ST_PointN(geom, i);
	            lon := ST_X(point);
	            lat := ST_Y(point);
	
	            -- Adjust longitude if crossing the anti-meridian
	            IF lon < -180 THEN
	                lon := lon + 360;
	            ELSIF lon > 180 THEN
	                lon := lon - 360;
	            END IF;
	
	            -- Add adjusted point to the new geometry
	            new_geom := ST_AddPoint(new_geom, ST_MakePoint(lon, lat));
	        END LOOP;
	
	    -- Add cases for other geometry types as needed
	    ELSE
	        RAISE EXCEPTION 'Unsupported geometry type: %', ST_GeometryType(geom);
	    END IF;
		RETURN new_geom;
    ELSE
        RETURN h3_cell_to_boundary(h3index)::geometry;
    END IF;
END;
$$ LANGUAGE plpgsql;

/*
DROP TABLE IF EXISTS basic.h3_grid_resolution_3; 
CREATE TABLE basic.h3_grid_resolution_3 AS 
SELECT basic.to_short_h3_3(h3_3::bigint) AS h3_3, h3_3 h3_3_text, ST_SETSRID(basic.fix_transmeridian_h3(h3_3), 4326) AS geom
FROM (
	SELECT h3_cell_to_children(h3_get_res_0_cells(), 3) AS h3_3
) x
*/