DROP FUNCTION IF EXISTS basic.fill_polygon_holes;
CREATE OR REPLACE FUNCTION basic.fill_polygon_holes(geom geometry, threshold float8)
RETURNS geometry AS $$
DECLARE
  outer_ring geometry;
  inner_ring geometry;
  num_rings integer;
  ring_index integer;
  new_rings geometry[];
BEGIN
  -- Function to remove small holes from a polygon
  -- threshold: minimum area of a hole to keep (in square meters)

  -- Ensure geometry is a valid polygon
    IF NOT ST_IsValid(geom) OR NOT ST_GeometryType(geom) = 'ST_Polygon' THEN
        RETURN NULL;
    END IF;

  -- Extract the outer ring
  outer_ring := ST_ExteriorRing(geom);
  
  -- Get the number of interior rings
  num_rings := ST_NumInteriorRings(geom);
  
  -- Initialize array to store remaining interior rings
  new_rings := ARRAY[]::geometry[];
  
  -- Loop through each interior ring
  FOR ring_index IN 1..num_rings LOOP
    -- Extract the current interior ring
    inner_ring := ST_InteriorRingN(geom, ring_index);
    
    -- Check if the area of the interior ring is larger than the threshold
    IF ST_Area(ST_MakePolygon(inner_ring)::geography) >= threshold THEN
      -- Add the ring to the new_rings array
      new_rings := array_append(new_rings, inner_ring);
    END IF;
  END LOOP;
  
  -- Construct a new polygon from the outer ring and the remaining interior rings
  RETURN ST_MakePolygon(outer_ring, new_rings) AS geom;
END;
$$ LANGUAGE plpgsql;
