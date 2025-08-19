-- Add UUID support for EA instances
-- This allows multiple instances of the same EA (same magic_number) to be tracked separately

-- Add UUID column to eas table
ALTER TABLE eas ADD COLUMN instance_uuid TEXT;

-- Remove UNIQUE constraint from magic_number by recreating the table
CREATE TABLE eas_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_uuid TEXT UNIQUE NOT NULL,
    magic_number INTEGER NOT NULL,  -- No longer unique
    symbol TEXT NOT NULL,
    strategy_tag TEXT NOT NULL,
    risk_config REAL DEFAULT 1.0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional fields to differentiate instances
    account_number TEXT,
    broker TEXT,
    timeframe TEXT DEFAULT 'M1',
    server_info TEXT,  -- Can store MT5 server details
    
    -- Create composite index for performance
    UNIQUE(instance_uuid)
);

-- Copy existing data with generated UUIDs
INSERT INTO eas_new (
    id, instance_uuid, magic_number, symbol, strategy_tag, 
    risk_config, status, created_at, last_seen
)
SELECT 
    id, 
    printf('%08x-%04x-%04x-%04x-%012x', 
        abs(random()), 
        abs(random()) & 0xFFFF,
        (abs(random()) & 0x0FFF) | 0x4000,
        (abs(random()) & 0x3FFF) | 0x8000,
        abs(random())
    ) as instance_uuid,
    magic_number, 
    symbol, 
    strategy_tag, 
    risk_config, 
    status, 
    created_at, 
    last_seen
FROM eas;

-- Drop old table and rename new one
DROP TABLE eas;
ALTER TABLE eas_new RENAME TO eas;

-- Create indexes for performance
CREATE INDEX idx_eas_magic_number ON eas(magic_number);
CREATE INDEX idx_eas_symbol ON eas(symbol);
CREATE INDEX idx_eas_status ON eas(status);
CREATE INDEX idx_eas_last_seen ON eas(last_seen);


