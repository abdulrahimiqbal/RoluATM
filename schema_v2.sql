-- RoluATM Enhanced Database Schema v2.0
-- Supports cloud-based transaction processing with Pi job polling

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enhanced transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kiosk_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    quarters INTEGER NOT NULL CHECK (quarters > 0),
    total DECIMAL(10,2) NOT NULL CHECK (total > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'paid', 'dispensing', 'completed', 'failed', 'expired')),
    mini_app_url TEXT,
    nullifier_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    paid_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Dispense jobs table (new)
CREATE TABLE IF NOT EXISTS dispense_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    kiosk_id UUID NOT NULL,
    quarters INTEGER NOT NULL CHECK (quarters > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3 CHECK (max_retries > 0),
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Kiosks table (new)
CREATE TABLE IF NOT EXISTS kiosks (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    location TEXT,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    hardware_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transaction events log (enhanced)
CREATE TABLE IF NOT EXISTS transaction_events (
    id SERIAL PRIMARY KEY,
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    job_id UUID REFERENCES dispense_jobs(id) ON DELETE SET NULL,
    kiosk_id UUID,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_kiosk_status ON transactions(kiosk_id, status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_expires_at ON transactions(expires_at);
CREATE INDEX IF NOT EXISTS idx_transactions_nullifier ON transactions(nullifier_hash);

CREATE INDEX IF NOT EXISTS idx_dispense_jobs_pending ON dispense_jobs(kiosk_id, status, created_at) 
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_dispense_jobs_retry ON dispense_jobs(kiosk_id, retry_count, max_retries)
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_dispense_jobs_transaction ON dispense_jobs(transaction_id);

CREATE INDEX IF NOT EXISTS idx_kiosks_status ON kiosks(status);
CREATE INDEX IF NOT EXISTS idx_kiosks_last_seen ON kiosks(last_seen_at);

CREATE INDEX IF NOT EXISTS idx_transaction_events_transaction_id ON transaction_events(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_events_type ON transaction_events(event_type);
CREATE INDEX IF NOT EXISTS idx_transaction_events_kiosk ON transaction_events(kiosk_id);

-- Add foreign key constraints
ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_kiosk 
FOREIGN KEY (kiosk_id) REFERENCES kiosks(id);

ALTER TABLE dispense_jobs 
ADD CONSTRAINT fk_dispense_jobs_kiosk 
FOREIGN KEY (kiosk_id) REFERENCES kiosks(id);

-- Useful views for monitoring
CREATE OR REPLACE VIEW kiosk_health AS
SELECT 
    k.id,
    k.name,
    k.location,
    k.status,
    k.last_seen_at,
    EXTRACT(EPOCH FROM (NOW() - k.last_seen_at)) / 60 AS minutes_since_last_seen,
    COUNT(dj.id) FILTER (WHERE dj.status = 'pending') AS pending_jobs,
    COUNT(dj.id) FILTER (WHERE dj.status = 'failed') AS failed_jobs,
    COUNT(t.id) FILTER (WHERE t.status = 'pending' AND t.created_at > NOW() - INTERVAL '1 hour') AS recent_transactions
FROM kiosks k
LEFT JOIN dispense_jobs dj ON k.id = dj.kiosk_id
LEFT JOIN transactions t ON k.id = t.kiosk_id
GROUP BY k.id, k.name, k.location, k.status, k.last_seen_at;

CREATE OR REPLACE VIEW transaction_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) AS hour,
    kiosk_id,
    status,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    SUM(quarters) AS total_quarters
FROM transactions
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), kiosk_id, status
ORDER BY hour DESC;

-- Functions for cleanup and maintenance
CREATE OR REPLACE FUNCTION cleanup_expired_transactions()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    -- Mark expired transactions
    UPDATE transactions 
    SET status = 'expired' 
    WHERE status = 'pending' 
      AND expires_at < NOW();
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    
    -- Log the cleanup
    INSERT INTO transaction_events (transaction_id, event_type, event_data)
    SELECT id, 'expired', jsonb_build_object('expired_at', NOW())
    FROM transactions 
    WHERE status = 'expired' 
      AND expires_at < NOW() - INTERVAL '1 minute';
    
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Function to retry failed jobs
CREATE OR REPLACE FUNCTION retry_failed_jobs(max_age_minutes INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    retry_count INTEGER;
BEGIN
    -- Reset failed jobs that are not too old and haven't exceeded max retries
    UPDATE dispense_jobs 
    SET status = 'pending', 
        retry_count = retry_count + 1,
        error_message = error_message || ' [AUTO-RETRY]'
    WHERE status = 'failed' 
      AND retry_count < max_retries
      AND last_attempt_at > NOW() - (max_age_minutes || ' minutes')::INTERVAL;
    
    GET DIAGNOSTICS retry_count = ROW_COUNT;
    
    RETURN retry_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically create transaction events
CREATE OR REPLACE FUNCTION log_transaction_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        INSERT INTO transaction_events (transaction_id, kiosk_id, event_type, event_data)
        VALUES (
            NEW.id, 
            NEW.kiosk_id,
            'status_change',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'changed_at', NOW()
            )
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transaction_status_change_trigger
    AFTER UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION log_transaction_status_change();

-- Sample data for testing (optional)
-- INSERT INTO kiosks (id, name, location) VALUES 
-- ('550e8400-e29b-41d4-a716-446655440000', 'Kiosk Alpha', 'Main Street Location'),
-- ('550e8400-e29b-41d4-a716-446655440001', 'Kiosk Beta', 'Mall Location');

-- Maintenance schedule (run these periodically)
-- SELECT cleanup_expired_transactions();
-- SELECT retry_failed_jobs(30);

COMMENT ON TABLE transactions IS 'Main transactions table with enhanced kiosk tracking';
COMMENT ON TABLE dispense_jobs IS 'Job queue for physical dispensing operations';
COMMENT ON TABLE kiosks IS 'Kiosk registration and health tracking';
COMMENT ON TABLE transaction_events IS 'Audit log for all transaction and job events';

COMMENT ON VIEW kiosk_health IS 'Real-time health status of all kiosks';
COMMENT ON VIEW transaction_summary IS 'Hourly transaction summary by kiosk';

COMMENT ON FUNCTION cleanup_expired_transactions() IS 'Marks expired transactions and logs events';
COMMENT ON FUNCTION retry_failed_jobs(INTEGER) IS 'Automatically retries failed dispense jobs'; 