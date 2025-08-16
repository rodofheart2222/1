-- Migration: Add EA Tagging and Grouping System
-- Date: 2024-12-08
-- Description: Add support for custom tags and grouping functionality for EAs

-- EA Tags table for custom tagging system
CREATE TABLE IF NOT EXISTS ea_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
    UNIQUE(ea_id, tag_name)
);

-- EA Groups table for predefined grouping
CREATE TABLE IF NOT EXISTS ea_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT UNIQUE NOT NULL,
    group_type TEXT NOT NULL CHECK (group_type IN ('symbol', 'strategy', 'risk_level', 'custom')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EA Group Memberships - many-to-many relationship
CREATE TABLE IF NOT EXISTS ea_group_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES ea_groups(id) ON DELETE CASCADE,
    UNIQUE(ea_id, group_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ea_tags_ea_id ON ea_tags(ea_id);
CREATE INDEX IF NOT EXISTS idx_ea_tags_tag_name ON ea_tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_ea_groups_type ON ea_groups(group_type);
CREATE INDEX IF NOT EXISTS idx_ea_group_memberships_ea_id ON ea_group_memberships(ea_id);
CREATE INDEX IF NOT EXISTS idx_ea_group_memberships_group_id ON ea_group_memberships(group_id);

-- Insert default groups based on existing EA data
INSERT OR IGNORE INTO ea_groups (group_name, group_type, description) 
SELECT DISTINCT 'Symbol_' || symbol, 'symbol', 'Auto-generated group for symbol ' || symbol
FROM eas;

INSERT OR IGNORE INTO ea_groups (group_name, group_type, description) 
SELECT DISTINCT 'Strategy_' || REPLACE(strategy_tag, ' ', '_'), 'strategy', 'Auto-generated group for strategy ' || strategy_tag
FROM eas;

INSERT OR IGNORE INTO ea_groups (group_name, group_type, description) 
SELECT DISTINCT 'Risk_' || CAST(ROUND(risk_config, 2) AS TEXT), 'risk_level', 'Auto-generated group for risk level ' || CAST(ROUND(risk_config, 2) AS TEXT)
FROM eas;

-- Auto-assign EAs to their respective groups
INSERT OR IGNORE INTO ea_group_memberships (ea_id, group_id)
SELECT e.id, g.id
FROM eas e
JOIN ea_groups g ON (
    (g.group_type = 'symbol' AND g.group_name = 'Symbol_' || e.symbol) OR
    (g.group_type = 'strategy' AND g.group_name = 'Strategy_' || REPLACE(e.strategy_tag, ' ', '_')) OR
    (g.group_type = 'risk_level' AND g.group_name = 'Risk_' || CAST(ROUND(e.risk_config, 2) AS TEXT))
);