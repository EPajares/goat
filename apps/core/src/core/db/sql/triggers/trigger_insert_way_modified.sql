CREATE OR REPLACE FUNCTION basic.trigger_insert_way_modified() 
RETURNS TRIGGER AS $trigger_insert_way_modified$
BEGIN
	PERFORM basic.network_modification(NEW.scenario_id); 
	RETURN NEW;
END;
$trigger_insert_way_modified$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_insert_way_modified ON customer.way_modified; 
CREATE TRIGGER trigger_insert_way_modified AFTER INSERT ON customer.way_modified
FOR EACH ROW EXECUTE PROCEDURE basic.trigger_insert_way_modified();