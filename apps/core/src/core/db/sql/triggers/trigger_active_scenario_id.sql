CREATE OR REPLACE FUNCTION basic.check_and_update_scenario_id()
RETURNS TRIGGER AS $$
BEGIN
    -- For update on project
    IF TG_OP = 'UPDATE' THEN
        IF NOT EXISTS (SELECT 1 FROM scenario WHERE id = NEW.active_scenario_id) THEN
            NEW.active_scenario_id := NULL;
        END IF;
        RETURN NEW;
    -- For delete on scenario
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE customer.project SET active_scenario_id = NULL WHERE active_scenario_id = OLD.id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for update on project
CREATE TRIGGER trigger_update_project
BEFORE UPDATE ON customer.project
FOR EACH ROW
EXECUTE FUNCTION basic.check_and_update_scenario_id();

-- Trigger for delete on scenario
CREATE TRIGGER trigger_delete_scenario
AFTER DELETE ON customer.scenario
FOR EACH ROW
EXECUTE FUNCTION basic.check_and_update_scenario_id();