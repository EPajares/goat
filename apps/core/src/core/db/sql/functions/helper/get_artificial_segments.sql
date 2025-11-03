DROP TYPE IF EXISTS basic.origin_segment;
CREATE TYPE basic.origin_segment AS (
    id INT, class_ TEXT, impedance_slope FLOAT8, impedance_slope_reverse FLOAT8,
    impedance_surface FLOAT8, maxspeed_forward INT, maxspeed_backward INT, source INT,
    target INT, geom GEOMETRY, h3_3 INT2, h3_6 INT, fraction FLOAT[], fraction_geom GEOMETRY[],
    point_id INT2[], point_geom GEOMETRY[]
);


DROP TYPE IF EXISTS basic.artificial_segment CASCADE;
CREATE TYPE basic.artificial_segment AS (
    point_id INT2, point_geom GEOMETRY, point_cell_index H3INDEX, point_h3_3 INT, old_id INT,
    id INT, length_m FLOAT, length_3857 FLOAT, class_ TEXT, impedance_slope FLOAT8,
    impedance_slope_reverse FLOAT8, impedance_surface FLOAT8, coordinates_3857 JSONB,
    maxspeed_forward INT, maxspeed_backward INT, source INT, target INT, geom GEOMETRY,
    h3_3 INT2, h3_6 INT
);


DROP FUNCTION IF EXISTS basic.get_artificial_segments;
CREATE OR REPLACE FUNCTION basic.get_artificial_segments(
    street_network_edge_layer_id UUID,
    network_modifications_table TEXT,
    origin_points_table TEXT,
    num_origin_points INT,
    classes TEXT,
    point_cell_resolution INT,
    additional_filters TEXT
)
RETURNS SETOF basic.artificial_segment
LANGUAGE plpgsql
AS $function$
DECLARE
	-- Compute the maximum allowed snapping distance between origin points and the street network
	origin_buffer_dist FLOAT := (SELECT GREATEST(100, h3_get_hexagon_edge_length_avg(point_cell_resolution, 'm')));

	edge_network_table TEXT := 'user_data.street_network_line_' || REPLACE((
		SELECT user_id FROM customer.layer WHERE id = street_network_edge_layer_id
	)::TEXT, '-', '');

    combined_network_table TEXT;

    custom_cursor REFCURSOR;
	origin_segment basic.origin_segment;
	artificial_segment basic.artificial_segment;

    -- Increment everytime a new artificial segment is created
    artificial_seg_index INT = 1000000000; -- Defaults to 1 billion

    -- Increment everytime a new artificial connector/node is created
    artificial_con_index INT = 1000000000; -- Defaults to 1 billion

    -- Increment everytime a new artificial origin node is created (for isochrone starting points)
    artifical_origin_index INT = 2000000000; -- Defaults to 2 billion

    fraction FLOAT;
    new_geom GEOMETRY;
BEGIN
    
    IF network_modifications_table IS NOT NULL THEN
        SELECT REPLACE(
            '"' || 'temporal.' || basic.uuid_generate_v7() || '"',
            '-', '_'
        ) INTO combined_network_table;

        EXECUTE FORMAT(
            'CREATE TABLE %s AS
                WITH origin AS  (
                    SELECT
                        id, geom,
                        ST_SETSRID(ST_Buffer(geom::geography, %s)::GEOMETRY, 4326) AS buffer_geom,
                        basic.to_short_h3_3(h3_lat_lng_to_cell(ST_Centroid(geom)::point, 3)::bigint) AS h3_3
                    FROM %s
                    LIMIT %s::int
                )
                SELECT original_features.*
                FROM (
                    SELECT s.edge_id, s.class_, s.source, s.target, s.length_m, s.length_3857,
                        s.coordinates_3857, s.impedance_slope, s.impedance_slope_reverse,
                        s.impedance_surface, s.maxspeed_forward, s.maxspeed_backward, s.geom,
                        s.h3_6, s.h3_3
                    FROM %s s, origin o
                    WHERE ST_Intersects(s.geom, o.buffer_geom)
                ) original_features
                LEFT JOIN %I scenario_features ON original_features.edge_id = scenario_features.id
                WHERE scenario_features.id IS NULL
                UNION ALL
                SELECT s.id AS edge_id, class_, source, target, length_m, length_3857,
                    coordinates_3857::json, impedance_slope, impedance_slope_reverse,
                    impedance_surface, maxspeed_forward, maxspeed_backward, s.geom,
                    h3_6, s.h3_3
                FROM %I s, origin o
                WHERE ST_Intersects(s.geom, o.buffer_geom)
                AND edit_type = ''n'';',
                combined_network_table, origin_buffer_dist, origin_points_table, num_origin_points,
				edge_network_table, network_modifications_table, network_modifications_table
        );

        EXECUTE FORMAT(
            'SELECT create_distributed_table(''%s'', ''h3_3'');',
            combined_network_table
        );
    ELSE
        combined_network_table := edge_network_table;
    END IF;

	OPEN custom_cursor FOR EXECUTE
		FORMAT (
            'WITH origin AS  (
                SELECT
                    id, geom,
                    ST_SETSRID(ST_Buffer(geom::geography, %s)::GEOMETRY, 4326) AS buffer_geom,
                    basic.to_short_h3_3(h3_lat_lng_to_cell(ST_Centroid(geom)::point, 3)::bigint) AS h3_3
                FROM %s
                LIMIT %s::int
            ),
            best_segment AS (
                SELECT DISTINCT ON (o.id)
                    o.id AS point_id, o.geom AS point_geom, o.buffer_geom AS point_buffer,
                    s.edge_id AS id, s.class_, s.impedance_slope, s.impedance_slope_reverse,
                    s.impedance_surface, s.maxspeed_forward, s.maxspeed_backward,
                    s."source", s.target, s.geom, s.h3_3, s.h3_6,
                    ST_LineLocatePoint(s.geom, o.geom) AS fraction,
                    ST_ClosestPoint(s.geom, o.geom) AS fraction_geom
                FROM %s s, origin o
                WHERE class_ = ANY(string_to_array(''%s'', '',''))
                AND ST_Intersects(s.geom, o.buffer_geom)
                %s
                ORDER BY o.id, ST_ClosestPoint(s.geom, o.geom) <-> o.geom
            )
            SELECT
                bs.id, bs.class_, bs.impedance_slope,
                bs.impedance_slope_reverse, bs.impedance_surface,
                bs.maxspeed_forward, bs.maxspeed_backward, bs."source",
                bs.target, bs.geom, bs.h3_3, bs.h3_6,
                ARRAY_AGG(bs.fraction) AS fraction,
                ARRAY_AGG(bs.fraction_geom) AS fraction_geom,
                ARRAY_AGG(bs.point_id) AS point_id,
                ARRAY_AGG(bs.point_geom) AS point_geom
            FROM (SELECT * FROM best_segment ORDER BY fraction) bs
            GROUP BY
                bs.id, bs.class_, bs.impedance_slope, bs.impedance_slope_reverse,
                bs.impedance_surface, bs.maxspeed_forward, bs.maxspeed_backward,
                bs."source", bs.target, bs.geom, bs.h3_3, bs.h3_6;',
            origin_buffer_dist, origin_points_table, num_origin_points, combined_network_table,
			classes, additional_filters
        );
	LOOP
		FETCH custom_cursor INTO origin_segment;
		EXIT WHEN NOT FOUND;

        -- Assign values carried over from origin segment
        artificial_segment.old_id = origin_segment.id;
        artificial_segment.class_ = origin_segment.class_;
        artificial_segment.impedance_slope = origin_segment.impedance_slope;
        artificial_segment.impedance_slope_reverse = origin_segment.impedance_slope_reverse;
        artificial_segment.impedance_surface = origin_segment.impedance_surface;
        artificial_segment.maxspeed_forward = origin_segment.maxspeed_forward;
        artificial_segment.maxspeed_backward = origin_segment.maxspeed_backward;
        artificial_segment.h3_3 = origin_segment.h3_3;
        artificial_segment.h3_6 = origin_segment.h3_6;

        IF origin_segment.fraction[1] != 0 THEN
            -- Generate the first artifical segment for this origin segment
            artificial_segment.point_id = NULL;
            artificial_segment.point_geom = NULL;
            artificial_segment.point_cell_index = NULL;
            artificial_segment.point_h3_3 = NULL;
            artificial_segment.id = artificial_seg_index;
            new_geom = ST_LineSubstring(origin_segment.geom, 0, origin_segment.fraction[1]);
            artificial_segment.length_m = ST_Length(new_geom::geography);
            artificial_segment.length_3857 = ST_Length(ST_Transform(new_geom, 3857));
            artificial_segment.coordinates_3857 = (ST_AsGeoJSON(ST_Transform(new_geom, 3857))::jsonb)->'coordinates';
            artificial_segment.source = origin_segment.source;
            IF origin_segment.fraction[1] = 1 THEN
                artificial_segment.target = origin_segment.target;
            ELSE
                artificial_segment.target = artificial_con_index;
                artificial_con_index = artificial_con_index + 1;
            END IF;
            artificial_segment.geom = new_geom;
            RETURN NEXT artificial_segment;
            artificial_seg_index = artificial_seg_index + 1;
        END IF;

        -- Iterate over fractions if the origin segment is the origin for multiple isochrone starting points
        IF array_length(origin_segment.fraction, 1) > 1 THEN
            FOR i IN 2..array_length(origin_segment.fraction, 1) LOOP
                -- Generate an artificial segment connecting the origin point to the new artificial segment
                artificial_segment.point_id = origin_segment.point_id[i - 1];
                artificial_segment.point_geom = origin_segment.point_geom[i - 1];
                artificial_segment.point_cell_index = h3_lat_lng_to_cell(artificial_segment.point_geom::point, point_cell_resolution);
                artificial_segment.point_h3_3 = basic.to_short_h3_3(h3_lat_lng_to_cell(artificial_segment.point_geom::point, 3)::bigint);
                artificial_segment.id = artificial_seg_index;
                new_geom = ST_SetSRID(ST_MakeLine(
                    origin_segment.point_geom[i - 1],
                    origin_segment.fraction_geom[i - 1]
                ), 4326);
                artificial_segment.length_m = ST_Length(new_geom::geography);
                artificial_segment.length_3857 = ST_Length(ST_Transform(new_geom, 3857));
                artificial_segment.coordinates_3857 = (ST_AsGeoJSON(ST_Transform(new_geom, 3857))::jsonb)->'coordinates';
                artificial_segment.maxspeed_forward = 30;
                artificial_segment.maxspeed_backward = 30;
                artificial_segment.source = artifical_origin_index;
                artifical_origin_index = artifical_origin_index + 1;
                IF origin_segment.fraction[i - 1] = 0 THEN
                    artificial_segment.target = origin_segment.source;
                ELSIF origin_segment.fraction[i] = 1 THEN
                    artificial_segment.target = origin_segment.target;
                ELSE
                    artificial_segment.target = artificial_con_index - 1;
                END IF;
                artificial_segment.geom = new_geom;
                RETURN NEXT artificial_segment;
                artificial_seg_index = artificial_seg_index + 1;

                IF origin_segment.fraction[i] != origin_segment.fraction[i - 1] THEN
                    artificial_segment.point_id = NULL;
                    artificial_segment.point_geom = NULL;
                    artificial_segment.point_cell_index = NULL;
                    artificial_segment.point_h3_3 = NULL;
                    artificial_segment.id = artificial_seg_index;
                    new_geom = ST_LineSubstring(origin_segment.geom, origin_segment.fraction[i - 1], origin_segment.fraction[i]);
                    artificial_segment.length_m = ST_Length(new_geom::geography);
                    artificial_segment.length_3857 = ST_Length(ST_Transform(new_geom, 3857));
                    artificial_segment.coordinates_3857 = (ST_AsGeoJSON(ST_Transform(new_geom, 3857))::jsonb)->'coordinates';
                    IF origin_segment.fraction[i - 1] = 0 THEN
                        artificial_segment.source = origin_segment.source;
                    ELSE
                        artificial_segment.source = artificial_con_index - 1;
                    END IF;
                    IF origin_segment.fraction[i] = 1 THEN
                        artificial_segment.target = origin_segment.target;
                    ELSE
                        artificial_segment.target = artificial_con_index;
                        artificial_con_index = artificial_con_index + 1;
                    END IF;
                    artificial_segment.geom = new_geom;
                    RETURN NEXT artificial_segment;
                    artificial_seg_index = artificial_seg_index + 1;
                END IF;
            END LOOP;
        END IF;

        -- Generate an artificial segment connecting the origin point to the new artificial segment
        artificial_segment.point_id = origin_segment.point_id[array_length(origin_segment.point_id, 1)];
        artificial_segment.point_geom = origin_segment.point_geom[array_length(origin_segment.point_geom, 1)];
        artificial_segment.point_cell_index = h3_lat_lng_to_cell(artificial_segment.point_geom::point, point_cell_resolution);
        artificial_segment.point_h3_3 = basic.to_short_h3_3(h3_lat_lng_to_cell(artificial_segment.point_geom::point, 3)::bigint);
        artificial_segment.id = artificial_seg_index;
        new_geom = ST_SetSRID(ST_MakeLine(
            origin_segment.point_geom[array_length(origin_segment.point_geom, 1)],
            origin_segment.fraction_geom[array_length(origin_segment.fraction_geom, 1)]
        ), 4326);
        artificial_segment.length_m = ST_Length(new_geom::geography);
        artificial_segment.length_3857 = ST_Length(ST_Transform(new_geom, 3857));
        artificial_segment.coordinates_3857 = (ST_AsGeoJSON(ST_Transform(new_geom, 3857))::jsonb)->'coordinates';
        artificial_segment.maxspeed_forward = 30;
        artificial_segment.maxspeed_backward = 30;
        artificial_segment.source = artifical_origin_index;
        artifical_origin_index = artifical_origin_index + 1;
        IF origin_segment.fraction[array_length(origin_segment.fraction, 1)] = 0 THEN
            artificial_segment.target = origin_segment.source;
        ELSIF origin_segment.fraction[array_length(origin_segment.fraction, 1)] = 1 THEN
            artificial_segment.target = origin_segment.target;
        ELSE
            artificial_segment.target = artificial_con_index - 1;
        END IF;
        artificial_segment.geom = new_geom;
        RETURN NEXT artificial_segment;
        artificial_seg_index = artificial_seg_index + 1;

        IF origin_segment.fraction[array_length(origin_segment.fraction, 1)] != 1 THEN
            -- Generate the last artificial segment for this origin segment
            artificial_segment.point_id = NULL;
            artificial_segment.point_geom = NULL;
            artificial_segment.point_cell_index = NULL;
            artificial_segment.point_h3_3 = NULL;
            artificial_segment.id = artificial_seg_index;
            new_geom = ST_LineSubstring(origin_segment.geom, origin_segment.fraction[array_length(origin_segment.fraction, 1)], 1);
            artificial_segment.length_m = ST_Length(new_geom::geography);
            artificial_segment.length_3857 = ST_Length(ST_Transform(new_geom, 3857));
            artificial_segment.coordinates_3857 = (ST_AsGeoJSON(ST_Transform(new_geom, 3857))::jsonb)->'coordinates';
            IF origin_segment.fraction[array_length(origin_segment.fraction, 1)] = 0 THEN
                artificial_segment.source = origin_segment.source;
            ELSE
                artificial_segment.source = artificial_con_index - 1;
            END IF;
            artificial_segment.target = origin_segment.target;
            artificial_segment.geom = new_geom;
            RETURN NEXT artificial_segment;
            artificial_seg_index = artificial_seg_index + 1;
        END IF;
	
	END LOOP;
	
	CLOSE custom_cursor;

    IF network_modifications_table IS NOT NULL THEN
        EXECUTE FORMAT(
            'DROP TABLE IF EXISTS %s;',
            combined_network_table
        );
    END IF;
	
END;
$function$
