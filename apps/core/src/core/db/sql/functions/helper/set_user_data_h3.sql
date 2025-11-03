DROP FUNCTION IF EXISTS basic.set_user_data_h3();
CREATE OR REPLACE FUNCTION basic.set_user_data_h3()
RETURNS TRIGGER AS $$
BEGIN
  NEW.h3_3 := basic.to_short_h3_3(h3_lat_lng_to_cell(ST_CENTROID(NEW.geom)::point, 3)::bigint);
  NEW.h3_group := h3_lat_lng_to_cell(ST_CENTROID(NEW.geom)::point, 8);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;