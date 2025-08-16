-- Migration: Initial Schema
-- Created: 2024-12-08T00:00:01

-- This migration creates the initial database schema for MT5 COC Dashboard
-- Based on the design document requirements

-- EA Registry and Configuration
CREATE TABLE IF NOT EXISTS eas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    magic_number INTEGER UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    strategy_tag TEXT NOT NULL,
    risk_config REAL DEFAULT 1.0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Real-time EA Status
CREATE TABLE IF NOT EXISTS ea_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_profit REAL DEFAULT 0.0,
    open_positions INTEGER DEFAULT 0,
    sl_value REAL,
    tp_value REAL,
    trailing_active BOOLEAN DEFAULT FALSE,
    module_status TEXT, -- JSON format
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
);

-- Performance Metrics History
CREATE TABLE IF NOT EXISTS performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    date DATE DEFAULT (DATE('now')),
    total_profit REAL DEFAULT 0.0,
    profit_factor REAL DEFAULT 0.0,
    expected_payoff REAL DEFAULT 0.0,
    drawdown REAL DEFAULT 0.0,
    z_score REAL DEFAULT 0.0,
    trade_count INTEGER DEFAULT 0,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
);

-- Trade Journal
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    order_type TEXT NOT NULL,
    volume REAL NOT NULL,
    open_price REAL NOT NULL,
    close_price REAL,
    profit REAL DEFAULT 0.0,
    open_time TIMESTAMP NOT NULL,
    close_time TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
);

-- Backtest Benchmarks
CREATE TABLE IF NOT EXISTS backtest_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    profit_factor REAL NOT NULL,
    expected_payoff REAL NOT NULL,
    drawdown REAL NOT NULL,
    win_rate REAL NOT NULL,
    trade_count INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
);

-- News Events
CREATE TABLE IF NOT EXISTS news_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TIMESTAMP NOT NULL,
    currency TEXT NOT NULL,
    impact_level TEXT NOT NULL CHECK (impact_level IN ('high', 'medium', 'low')),
    description TEXT NOT NULL,
    pre_minutes INTEGER DEFAULT 30,
    post_minutes INTEGER DEFAULT 30
);

-- Command Queue
CREATE TABLE IF NOT EXISTS command_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER,
    command_type TEXT NOT NULL,
    command_data TEXT, -- JSON format
    scheduled_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_eas_magic_number ON eas(magic_number);
CREATE INDEX IF NOT EXISTS idx_eas_symbol ON eas(symbol);
CREATE INDEX IF NOT EXISTS idx_eas_strategy_tag ON eas(strategy_tag);
CREATE INDEX IF NOT EXISTS idx_ea_status_ea_id ON ea_status(ea_id);
CREATE INDEX IF NOT EXISTS idx_ea_status_timestamp ON ea_status(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_history_ea_id ON performance_history(ea_id);
CREATE INDEX IF NOT EXISTS idx_performance_history_date ON performance_history(date);
CREATE INDEX IF NOT EXISTS idx_trades_ea_id ON trades(ea_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_open_time ON trades(open_time);
CREATE INDEX IF NOT EXISTS idx_news_events_time ON news_events(event_time);
CREATE INDEX IF NOT EXISTS idx_command_queue_ea_id ON command_queue(ea_id);
CREATE INDEX IF NOT EXISTS idx_command_queue_executed ON command_queue(executed);