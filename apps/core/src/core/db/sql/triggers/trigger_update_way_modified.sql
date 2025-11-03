CREATE OR REPLACE FUNCTION basic.trigger_update_way_modified() 
RETURNS TRIGGER AS $trigger_update_way_modified$
BEGIN
	PERFORM basic.network_modification(NEW.scenario_id); 
	RETURN NEW;
END;
$trigger_update_way_modified$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_way_modified ON customer.way_modified; 
CREATE TRIGGER trigger_update_way_modified AFTER UPDATE ON customer.way_modified
FOR EACH ROW EXECUTE PROCEDURE basic.trigger_update_way_modified();