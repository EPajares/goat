LISTEN layer_changes;
DROP FUNCTION IF EXISTS customer.trigger_layer_changes() CASCADE; 
CREATE OR REPLACE FUNCTION customer.trigger_layer_changes() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM pg_notify('layer_changes', 'DELETE:' || REPLACE(OLD.id::text, '-', ''));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM pg_notify('layer_changes', 'UPDATE:' || REPLACE(OLD.id::text, '-', ''));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN 
        PERFORM pg_notify('layer_changes', 'INSERT:' || REPLACE(NEW.id::text, '-', ''));
        RETURN NEW; 
    END IF;
    RETURN NULL;  -- Just to handle other unexpected operations, though it's unlikely.
END;
$$ LANGUAGE plpgsql;

-- Drop the existing trigger
DROP TRIGGER IF EXISTS layer_changes_trigger ON customer.layer;

-- Recreate the trigger with conditions
CREATE TRIGGER layer_changes_trigger
AFTER INSERT OR UPDATE OR DELETE ON customer.layer
FOR EACH ROW 
EXECUTE FUNCTION customer.trigger_layer_changes();