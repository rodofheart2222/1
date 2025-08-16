# EA Grouping and Tagging System

## Overview

The EA Grouping and Tagging System provides comprehensive organization and management capabilities for Expert Advisors (EAs) in the MT5 COC Dashboard. This system allows users to group EAs by various criteria, apply custom tags, and execute mass commands on filtered sets of EAs.

## Features

### 1. EA Tagging System
- **Custom Tags**: Add custom key-value tags to any EA
- **Tag Management**: Add, remove, and update tags dynamically
- **Tag-based Filtering**: Find EAs based on tag criteria
- **Tag Statistics**: View usage statistics for all tags

### 2. EA Grouping System
- **Predefined Groups**: Automatic grouping by Symbol, Strategy, and Risk Level
- **Custom Groups**: Create custom groups for specific organizational needs
- **Group Management**: Add/remove EAs from groups dynamically
- **Auto-grouping**: Automatically create and populate groups based on EA attributes

### 3. Mass Command Execution
- **Group-based Commands**: Execute commands on all EAs in specific groups
- **Tag-based Commands**: Execute commands on EAs matching tag criteria
- **Multi-criteria Filtering**: Combine multiple filters for precise EA selection
- **Supported Commands**: Pause, Resume, Adjust Risk, Close Positions

### 4. Advanced Filtering
- **Multi-dimensional Filtering**: Filter by Symbol, Strategy, Risk Level, Status, Tags, and Groups
- **Complex Queries**: Combine multiple criteria for sophisticated EA selection
- **Real-time Updates**: All filtering and grouping data updates in real-time

## Database Schema

### EA Tags Table
```sql
CREATE TABLE ea_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
    UNIQUE(ea_id, tag_name)
);
```

### EA Groups Table
```sql
CREATE TABLE ea_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT UNIQUE NOT NULL,
    group_type TEXT NOT NULL CHECK (group_type IN ('symbol', 'strategy', 'risk_level', 'custom')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### EA Group Memberships Table
```sql
CREATE TABLE ea_group_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES ea_groups(id) ON DELETE CASCADE,
    UNIQUE(ea_id, group_id)
);
```

## API Reference

### EAGroupingService Class

#### Tag Management Methods

```python
# Add a tag to an EA
add_tag(ea_id: int, tag_name: str, tag_value: Optional[str] = None) -> bool

# Remove a tag from an EA
remove_tag(ea_id: int, tag_name: str) -> bool

# Get all tags for an EA
get_ea_tags(ea_id: int) -> Dict[str, str]

# Find EAs by tag criteria
find_eas_by_tag(tag_name: str, tag_value: Optional[str] = None) -> List[EA]

# Get all unique tag names
get_all_tag_names() -> List[str]

# Get tag usage statistics
get_tag_usage_stats() -> Dict[str, int]
```

#### Group Management Methods

```python
# Create a new EA group
create_group(group_name: str, group_type: str, description: Optional[str] = None) -> Optional[EAGroup]

# Delete an EA group
delete_group(group_id: int) -> bool

# Add an EA to a group
add_ea_to_group(ea_id: int, group_id: int) -> bool

# Remove an EA from a group
remove_ea_from_group(ea_id: int, group_id: int) -> bool

# Get all EAs in a group
get_group_members(group_id: int) -> List[EA]

# Get all groups an EA belongs to
get_ea_groups(ea_id: int) -> List[EAGroup]

# Get all groups, optionally filtered by type
get_all_groups(group_type: Optional[str] = None) -> List[EAGroup]
```

#### Auto-grouping Methods

```python
# Automatically create and populate symbol-based groups
auto_group_by_symbol() -> Dict[str, int]

# Automatically create and populate strategy-based groups
auto_group_by_strategy() -> Dict[str, int]

# Automatically create and populate risk level-based groups
auto_group_by_risk_level() -> Dict[float, int]
```

#### Advanced Filtering and Command Execution

```python
# Find EAs by multiple criteria
find_eas_by_criteria(
    symbols: Optional[List[str]] = None,
    strategy_tags: Optional[List[str]] = None,
    risk_levels: Optional[List[float]] = None,
    statuses: Optional[List[str]] = None,
    tags: Optional[Dict[str, str]] = None,
    groups: Optional[List[str]] = None
) -> List[EA]

# Execute command on EAs matching tag criteria
execute_command_by_tags(
    command_type: str,
    tags: Dict[str, str],
    parameters: Optional[Dict[str, Any]] = None,
    scheduled_time: Optional[datetime] = None
) -> List[Command]

# Execute command on EAs in specified groups
execute_command_by_groups(
    command_type: str,
    group_names: List[str],
    parameters: Optional[Dict[str, Any]] = None,
    scheduled_time: Optional[datetime] = None
) -> List[Command]
```

## WebSocket Events

### Client to Server Events

```javascript
// Group management
socket.emit('create_group', {
    group_name: 'My Group',
    group_type: 'custom',
    description: 'Description'
});

socket.emit('delete_group', { group_id: 1 });
socket.emit('add_ea_to_group', { ea_id: 1, group_id: 1 });
socket.emit('remove_ea_from_group', { ea_id: 1, group_id: 1 });

// Auto-grouping
socket.emit('auto_group_by_symbol');
socket.emit('auto_group_by_strategy');
socket.emit('auto_group_by_risk_level');

// Tag management
socket.emit('add_ea_tag', {
    ea_id: 1,
    tag_name: 'environment',
    tag_value: 'production'
});

socket.emit('remove_ea_tag', { ea_id: 1, tag_name: 'environment' });

// Command execution
socket.emit('execute_command_by_groups', {
    command_type: 'pause',
    group_names: ['Symbol_EURUSD'],
    parameters: {}
});

socket.emit('execute_command_by_tags', {
    command_type: 'adjust_risk',
    tags: { environment: 'production' },
    parameters: { new_risk_level: 1.5 }
});
```

### Server to Client Events

```javascript
// Data updates
socket.on('grouping_data_update', (data) => {
    // data.groups - array of group objects
    // data.eas - array of EA objects with tags and groups
    // data.tag_stats - tag usage statistics
});

socket.on('grouping_stats_update', (stats) => {
    // stats.total_eas, total_groups, total_tags, etc.
});

// Command execution results
socket.on('command_execution_result', (result) => {
    // result.success, affected_eas, command_type, execution_method
});

// Individual operation results
socket.on('group_created', (result) => {
    // result.success, group
});

socket.on('tag_added', (result) => {
    // result.success
});
```

## Usage Examples

### Basic Tag Management

```python
from backend.services.ea_grouping_service import EAGroupingService

service = EAGroupingService()

# Add tags to an EA
service.add_tag(ea_id=1, tag_name='environment', tag_value='production')
service.add_tag(ea_id=1, tag_name='version', tag_value='v2.1')
service.add_tag(ea_id=1, tag_name='active')  # Tag without value

# Get EA tags
tags = service.get_ea_tags(ea_id=1)
# Returns: {'environment': 'production', 'version': 'v2.1', 'active': None}

# Find EAs by tag
prod_eas = service.find_eas_by_tag('environment', 'production')
active_eas = service.find_eas_by_tag('active')  # Any value
```

### Group Management

```python
# Create a custom group
group = service.create_group('High Risk EAs', 'custom', 'EAs with risk > 2.0')

# Add EAs to the group
service.add_ea_to_group(ea_id=1, group_id=group.id)
service.add_ea_to_group(ea_id=2, group_id=group.id)

# Auto-create groups
symbol_groups = service.auto_group_by_symbol()
strategy_groups = service.auto_group_by_strategy()
risk_groups = service.auto_group_by_risk_level()
```

### Advanced Filtering and Commands

```python
# Find EAs matching multiple criteria
matching_eas = service.find_eas_by_criteria(
    symbols=['EURUSD', 'GBPUSD'],
    strategy_tags=['Compression v1'],
    tags={'environment': 'production'},
    groups=['High Risk EAs']
)

# Execute commands on filtered EAs
commands = service.execute_command_by_tags(
    command_type='pause',
    tags={'environment': 'test'},
    parameters={}
)

commands = service.execute_command_by_groups(
    command_type='adjust_risk',
    group_names=['Symbol_EURUSD', 'Strategy_Compression_v1'],
    parameters={'new_risk_level': 1.2}
)
```

### Frontend Integration

```javascript
// React component usage
import EAGroupingPanel from './EAGroupingPanel';

const MyDashboard = () => {
    return (
        <div>
            <EAGroupingPanel />
        </div>
    );
};
```

## Requirements Mapping

This implementation addresses the following requirements from the specification:

### Requirement 5.1: EA Grouping by Symbol, Strategy Name, and Risk Level
-  Implemented auto-grouping methods for all three criteria
-  Groups are automatically created and populated
-  EAs are assigned to appropriate groups based on their attributes

### Requirement 5.2: Custom Tag Management System
-  Custom tags with optional values
-  Tag CRUD operations (Create, Read, Update, Delete)
-  Tag-based EA filtering and search

### Requirement 5.3: Commander Controls Based on Tags
-  Mass command execution based on tag criteria
-  Integration with existing command dispatcher
-  Support for pause/resume operations via tags

### Requirement 5.4: Mass Commands to Filtered EAs
-  Group-based mass commands
-  Tag-based mass commands
-  Multi-criteria filtering for precise EA selection
-  Support for all command types (pause, resume, adjust_risk, close_positions)

## Testing

The system includes comprehensive tests covering:

- Tag management operations
- Group creation and membership management
- Auto-grouping functionality
- Advanced filtering capabilities
- Command execution workflows
- Database integrity and constraints

Run tests with:
```bash
python -m pytest backend/services/test_ea_grouping_service.py -v
python -m backend.services.test_ea_grouping_integration
```

## Performance Considerations

- Database indexes on frequently queried columns (ea_id, tag_name, group_id)
- Efficient SQL queries with proper joins and filtering
- Caching of frequently accessed data
- Batch operations for mass command execution
- Real-time WebSocket updates for UI responsiveness

## Security Considerations

- Input validation for all tag names and values
- SQL injection prevention through parameterized queries
- Command execution authorization checks
- Audit logging for all grouping and tagging operations
- Rate limiting for mass command operations

## Future Enhancements

- **Tag Hierarchies**: Support for nested tag structures
- **Group Templates**: Predefined group templates for common use cases
- **Conditional Grouping**: Dynamic groups based on real-time EA performance
- **Tag Automation**: Automatic tag assignment based on EA behavior
- **Export/Import**: Backup and restore grouping configurations
- **Advanced Analytics**: Performance analysis by groups and tags