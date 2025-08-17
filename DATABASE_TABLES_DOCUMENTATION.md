# Database Tables Documentation

## Overview
The MT5 Dashboard database has been properly set up with all required tables for production use. All tables are created with proper foreign key relationships and indexes for optimal performance.

## Database Location
- **Path**: `data/mt5_dashboard.db`
- **Type**: SQLite3
- **Backup**: Automatically created at `data/mt5_dashboard.db.backup_YYYYMMDD_HHMMSS`

## Tables Structure

### 1. **eas** - Expert Advisors Registry
Main table for tracking all EAs in the system.

**Columns:**
- `id` - Primary key
- `magic_number` - Unique EA identifier (UNIQUE constraint)
- `symbol` - Trading symbol (e.g., EURUSD)
- `strategy_tag` - Strategy identifier
- `risk_config` - Risk configuration (default: 1.0)
- `status` - EA status: 'active', 'paused', or 'error'
- `ea_name` - EA display name
- `timeframe` - Trading timeframe (default: 'M1')
- `last_heartbeat` - Last communication timestamp
- `account_number` - MT5 account number
- `broker` - Broker name
- `balance`, `equity`, `margin`, `free_margin`, `margin_level` - Account metrics
- `total_trades`, `active_trades` - Trade counters
- `total_profit` - Total profit/loss
- `created_at`, `updated_at`, `last_seen` - Timestamps

**Indexes:**
- `idx_eas_magic_number`
- `idx_eas_symbol`
- `idx_eas_strategy_tag`
- `idx_eas_status`

### 2. **ea_status** - Real-time EA Status Snapshots
Stores periodic status updates from EAs.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `timestamp` - Snapshot time
- `current_profit` - Current P&L
- `open_positions` - Number of open positions
- `sl_value` - Stop loss value
- `tp_value` - Take profit value
- `trailing_active` - Trailing stop status
- `module_status` - JSON status of EA modules

**Indexes:**
- `idx_ea_status_ea_id`
- `idx_ea_status_timestamp`

### 3. **trades** - Trade Journal
Records all trades executed by EAs.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `trade_id` - Unique trade identifier
- `magic_number` - EA magic number
- `symbol` - Trading symbol
- `order_type`, `trade_type` - Order/trade type
- `volume` - Trade volume/lot size
- `open_price`, `close_price` - Entry/exit prices
- `requested_price`, `actual_price` - Requested vs actual prices
- `sl`, `tp` - Stop loss and take profit
- `status` - Trade status (default: 'pending')
- `profit`, `commission`, `swap` - Financial metrics
- `comment` - Trade comment
- `mt5_ticket` - MT5 ticket number
- `risk_percent`, `account_balance`, `position_size_usd` - Risk metrics
- Various timestamps: `open_time`, `close_time`, `request_time`, `fill_time`, `created_at`, `updated_at`

**Indexes:**
- `idx_trades_ea_id`
- `idx_trades_symbol`
- `idx_trades_open_time`
- `idx_trades_magic_number`
- `idx_trades_status`

### 4. **performance_history** - Daily Performance Metrics
Stores daily performance snapshots for each EA.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `date` - Performance date
- `total_profit` - Total profit for the day
- `profit_factor` - Profit factor metric
- `expected_payoff` - Expected payoff per trade
- `drawdown` - Maximum drawdown
- `z_score` - Statistical z-score
- `trade_count` - Number of trades

**Indexes:**
- `idx_performance_history_ea_id`
- `idx_performance_history_date`

### 5. **backtest_benchmarks** - Backtest Results
Stores backtest benchmark data for comparison with live performance.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `magic_number` - EA magic number
- `profit_factor` - Backtest profit factor
- `expected_payoff` - Expected payoff
- `drawdown` - Maximum drawdown
- `win_rate` - Win rate percentage
- `trade_count` - Total trades in backtest
- `upload_date` - When backtest was uploaded

### 6. **news_events** - Economic Calendar
Stores news events for trading restrictions.

**Columns:**
- `id` - Primary key
- `event_time` - Event timestamp
- `currency` - Affected currency
- `impact_level` - 'high', 'medium', or 'low'
- `description` - Event description
- `pre_minutes` - Blackout before event (default: 30)
- `post_minutes` - Blackout after event (default: 30)

**Indexes:**
- `idx_news_events_time`

### 7. **command_queue** - EA Command Queue
Queues commands to be sent to EAs.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `command_type` - Type of command
- `command_data` - JSON command parameters
- `scheduled_time` - When to execute
- `executed` - Execution status
- `created_at` - Creation timestamp

**Indexes:**
- `idx_command_queue_ea_id`
- `idx_command_queue_executed`

### 8. **commands** - Command History
Records all commands sent to EAs.

**Columns:**
- `id` - Primary key
- `command_id` - Unique command identifier
- `magic_number` - Target EA
- `command_type` - Command type
- `parameters` - Command parameters
- `status` - Command status
- `response` - EA response
- `created_at`, `processed_at` - Timestamps

**Indexes:**
- `idx_commands_magic_number`
- `idx_commands_status`

### 9. **news** - News Articles
Stores news articles and analysis.

**Columns:**
- `id` - Primary key
- `title` - Article title
- `content` - Article content
- `impact` - Impact level
- `currency` - Related currency
- `event_time` - Event time
- `created_at` - Creation time

### 10. **backtests** - Backtest Records
Detailed backtest execution records.

**Columns:**
- `id` - Primary key
- `backtest_id` - Unique backtest identifier
- `ea_name` - EA name
- `symbol` - Trading symbol
- `timeframe` - Test timeframe
- `start_date`, `end_date` - Test period
- `initial_balance`, `final_balance` - Balance change
- `total_trades`, `winning_trades`, `losing_trades` - Trade statistics
- `profit_factor`, `max_drawdown`, `sharpe_ratio` - Performance metrics
- `parameters` - Test parameters (JSON)
- `results` - Detailed results (JSON)
- `status` - Test status
- `created_at`, `completed_at` - Timestamps

### 11. **ea_tags** - Custom EA Tags
Flexible tagging system for EAs.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `tag_name` - Tag name
- `tag_value` - Tag value
- `created_at` - Creation timestamp
- **Unique constraint**: (ea_id, tag_name)

**Indexes:**
- `idx_ea_tags_ea_id`
- `idx_ea_tags_tag_name`

### 12. **ea_groups** - EA Groups
Predefined groups for organizing EAs.

**Columns:**
- `id` - Primary key
- `group_name` - Unique group name
- `group_type` - 'symbol', 'strategy', 'risk_level', or 'custom'
- `description` - Group description
- `created_at` - Creation timestamp

**Indexes:**
- `idx_ea_groups_type`

### 13. **ea_group_memberships** - Group Membership
Many-to-many relationship between EAs and groups.

**Columns:**
- `id` - Primary key
- `ea_id` - Foreign key to eas table
- `group_id` - Foreign key to ea_groups table
- `added_at` - When EA was added to group
- **Unique constraint**: (ea_id, group_id)

**Indexes:**
- `idx_ea_group_memberships_ea_id`
- `idx_ea_group_memberships_group_id`

### 14. **schema_migrations** - Database Migrations
Tracks applied database migrations.

**Columns:**
- `id` - Primary key
- `version` - Migration version (UNIQUE)
- `name` - Migration name
- `applied_at` - When migration was applied
- `checksum` - Migration file checksum

## Foreign Key Relationships

1. **ea_status** → **eas** (ea_id → id)
2. **trades** → **eas** (ea_id → id)
3. **performance_history** → **eas** (ea_id → id)
4. **backtest_benchmarks** → **eas** (ea_id → id)
5. **command_queue** → **eas** (ea_id → id)
6. **ea_tags** → **eas** (ea_id → id)
7. **ea_group_memberships** → **eas** (ea_id → id)
8. **ea_group_memberships** → **ea_groups** (group_id → id)

All foreign key relationships use `ON DELETE CASCADE` to maintain referential integrity.

## Usage Notes

1. **Database Path**: The database is located at `data/mt5_dashboard.db` by default. This can be overridden with the `DATABASE_PATH` environment variable.

2. **Backups**: Always backup the database before major operations. Use the `recreate_database.py` script which automatically creates backups.

3. **Foreign Keys**: SQLite foreign keys must be enabled for each connection:
   ```sql
   PRAGMA foreign_keys = ON;
   ```

4. **JSON Fields**: Several fields store JSON data (module_status, command_data, parameters, results). Ensure proper JSON serialization when storing data.

5. **Timestamps**: All timestamps use SQLite's CURRENT_TIMESTAMP default where applicable.

6. **Indexes**: All frequently queried columns have indexes for optimal performance.

## Maintenance

To verify database integrity:
```bash
python3 fix_database_schema_simple.py
```

To recreate the database (with automatic backup):
```bash
python3 recreate_database.py
```

## Production Considerations

1. **Connection Pooling**: The backend uses connection pooling for SQLite. Each API route gets its own connection.

2. **Concurrent Access**: SQLite handles concurrent reads well but serializes writes. For high-traffic production, consider PostgreSQL or MySQL.

3. **Backup Strategy**: Implement regular automated backups, especially before deployments.

4. **Migration System**: Use the schema_migrations table to track database changes over time.

5. **Monitoring**: Monitor database size and performance, especially the ea_status and trades tables which grow rapidly.