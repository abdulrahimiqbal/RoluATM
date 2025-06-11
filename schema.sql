-- RoluATM Database Schema
-- Supports the new transaction-based flow with QR codes and mini app payments

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    quarters INTEGER NOT NULL CHECK (quarters > 0),
    total DECIMAL(10,2) NOT NULL CHECK (total > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'dispensing', 'complete', 'failed', 'expired')),
    mini_app_url TEXT,
    nullifier_hash VARCHAR(255),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    paid_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_expires_at ON transactions(expires_at);
CREATE INDEX IF NOT EXISTS idx_transactions_nullifier ON transactions(nullifier_hash);

-- Hardware status log
CREATE TABLE IF NOT EXISTS hardware_status_log (
    id SERIAL PRIMARY KEY,
    coin_dispenser_status VARCHAR(20),
    network_status VARCHAR(20),
    security_status VARCHAR(20),
    raw_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transaction events log (for debugging and analytics)
CREATE TABLE IF NOT EXISTS transaction_events (
    id SERIAL PRIMARY KEY,
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transaction_events_transaction_id ON transaction_events(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_events_type ON transaction_events(event_type);

-- Clean up expired transactions (run this periodically)
-- DELETE FROM transactions WHERE status = 'pending' AND expires_at < NOW() - INTERVAL '1 hour'; 