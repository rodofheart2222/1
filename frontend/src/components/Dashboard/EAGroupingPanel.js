import React, { useState, useEffect, useContext } from 'react';
import { useDashboard } from '../../context/DashboardContext';
import './EAGroupingPanel.css';

const EAGroupingPanel = () => {
  const { state } = useDashboard();
  const { eaData: eas } = state;
  const [activeTab, setActiveTab] = useState('groups');
  const [groups, setGroups] = useState([]);
  const [tags, setTags] = useState({});
  const [selectedEAs, setSelectedEAs] = useState([]);
  const [groupingStats, setGroupingStats] = useState({});
  const [loading, setLoading] = useState(false);
  
  // Group management state
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupType, setNewGroupType] = useState('custom');
  const [newGroupDescription, setNewGroupDescription] = useState('');
  
  // Tag management state
  const [selectedEAForTag, setSelectedEAForTag] = useState(null);
  const [newTagName, setNewTagName] = useState('');
  const [newTagValue, setNewTagValue] = useState('');
  
  // Command execution state
  const [commandType, setCommandType] = useState('pause');
  const [commandParameters, setCommandParameters] = useState('');
  const [filterCriteria, setFilterCriteria] = useState({
    symbols: [],
    strategies: [],
    groups: [],
    tags: {}
  });

  useEffect(() => {
    // Initialize with mock data for now
    // TODO: Integrate with WebSocket when available
    setGroups([
      { id: 1, group_name: 'Symbol_EURUSD', group_type: 'symbol', description: 'EURUSD pairs' },
      { id: 2, group_name: 'Strategy_Compression_v1', group_type: 'strategy', description: 'Compression strategy' }
    ]);
    setGroupingStats({
      total_eas: eas.length,
      total_groups: 2,
      total_tags: 0,
      total_memberships: 0,
      group_types: { symbol: 1, strategy: 1 },
      tag_usage: {}
    });
  }, [eas]);

  const handleGroupingDataUpdate = (data) => {
    setGroups(data.groups || []);
    setTags(data.tags || {});
  };

  const handleGroupingStatsUpdate = (stats) => {
    setGroupingStats(stats);
  };

  const handleCommandResult = (result) => {
    if (result.success) {
      alert(`Command executed successfully on ${result.affected_eas} EAs`);
    } else {
      alert(`Command failed: ${result.error}`);
    }
  };

  // Group Management Functions
  const createGroup = async () => {
    if (!newGroupName.trim()) {
      alert('Group name is required');
      return;
    }

    setLoading(true);
    try {
      // Mock group creation for now
      const newGroup = {
        id: Date.now(),
        group_name: newGroupName,
        group_type: newGroupType,
        description: newGroupDescription
      };
      
      setGroups(prev => [...prev, newGroup]);
      setNewGroupName('');
      setNewGroupDescription('');
      
      alert('Group created successfully (mock implementation)');
    } catch (error) {
      console.error('Error creating group:', error);
      alert('Failed to create group');
    } finally {
      setLoading(false);
    }
  };

  const deleteGroup = async (groupId) => {
    if (!confirm('Are you sure you want to delete this group?')) {
      return;
    }

    setLoading(true);
    try {
      setGroups(prev => prev.filter(group => group.id !== groupId));
      alert('Group deleted successfully (mock implementation)');
    } catch (error) {
      console.error('Error deleting group:', error);
      alert('Failed to delete group');
    } finally {
      setLoading(false);
    }
  };

  const addEAToGroup = async (eaId, groupId) => {
    setLoading(true);
    try {
      alert('EA added to group successfully (mock implementation)');
    } catch (error) {
      console.error('Error adding EA to group:', error);
      alert('Failed to add EA to group');
    } finally {
      setLoading(false);
    }
  };

  const removeEAFromGroup = async (eaId, groupId) => {
    setLoading(true);
    try {
      alert('EA removed from group successfully (mock implementation)');
    } catch (error) {
      console.error('Error removing EA from group:', error);
      alert('Failed to remove EA from group');
    } finally {
      setLoading(false);
    }
  };

  // Auto-grouping functions
  const autoGroupBySymbol = async () => {
    setLoading(true);
    try {
      // Mock auto-grouping by symbol
      const symbols = [...new Set(eas.map(ea => ea.symbol))];
      const newGroups = symbols.map(symbol => ({
        id: Date.now() + Math.random(),
        group_name: `Symbol_${symbol}`,
        group_type: 'symbol',
        description: `Auto-generated group for symbol ${symbol}`
      }));
      
      setGroups(prev => [...prev, ...newGroups]);
      alert(`Auto-grouped by symbol: created ${newGroups.length} groups (mock implementation)`);
    } catch (error) {
      console.error('Error auto-grouping by symbol:', error);
      alert('Failed to auto-group by symbol');
    } finally {
      setLoading(false);
    }
  };

  const autoGroupByStrategy = async () => {
    setLoading(true);
    try {
      // Mock auto-grouping by strategy
      const strategies = [...new Set(eas.map(ea => ea.strategy_tag))];
      const newGroups = strategies.map(strategy => ({
        id: Date.now() + Math.random(),
        group_name: `Strategy_${strategy.replace(' ', '_')}`,
        group_type: 'strategy',
        description: `Auto-generated group for strategy ${strategy}`
      }));
      
      setGroups(prev => [...prev, ...newGroups]);
      alert(`Auto-grouped by strategy: created ${newGroups.length} groups (mock implementation)`);
    } catch (error) {
      console.error('Error auto-grouping by strategy:', error);
      alert('Failed to auto-group by strategy');
    } finally {
      setLoading(false);
    }
  };

  const autoGroupByRiskLevel = async () => {
    setLoading(true);
    try {
      // Mock auto-grouping by risk level
      const riskLevels = [...new Set(eas.map(ea => ea.risk_config))];
      const newGroups = riskLevels.map(risk => ({
        id: Date.now() + Math.random(),
        group_name: `Risk_${risk}`,
        group_type: 'risk_level',
        description: `Auto-generated group for risk level ${risk}`
      }));
      
      setGroups(prev => [...prev, ...newGroups]);
      alert(`Auto-grouped by risk level: created ${newGroups.length} groups (mock implementation)`);
    } catch (error) {
      console.error('Error auto-grouping by risk level:', error);
      alert('Failed to auto-group by risk level');
    } finally {
      setLoading(false);
    }
  };

  // Tag Management Functions
  const addTag = async () => {
    if (!selectedEAForTag || !newTagName.trim()) {
      alert('Please select an EA and enter a tag name');
      return;
    }

    setLoading(true);
    try {
      // Mock tag addition
      setTags(prev => ({
        ...prev,
        [selectedEAForTag]: {
          ...prev[selectedEAForTag],
          [newTagName]: newTagValue || null
        }
      }));
      
      setNewTagName('');
      setNewTagValue('');
      alert('Tag added successfully (mock implementation)');
    } catch (error) {
      console.error('Error adding tag:', error);
      alert('Failed to add tag');
    } finally {
      setLoading(false);
    }
  };

  const removeTag = async (eaId, tagName) => {
    setLoading(true);
    try {
      // Mock tag removal
      setTags(prev => {
        const newTags = { ...prev };
        if (newTags[eaId]) {
          delete newTags[eaId][tagName];
          if (Object.keys(newTags[eaId]).length === 0) {
            delete newTags[eaId];
          }
        }
        return newTags;
      });
      alert('Tag removed successfully (mock implementation)');
    } catch (error) {
      console.error('Error removing tag:', error);
      alert('Failed to remove tag');
    } finally {
      setLoading(false);
    }
  };

  // Command Execution Functions
  const executeCommandByGroups = async () => {
    if (filterCriteria.groups.length === 0) {
      alert('Please select at least one group');
      return;
    }

    setLoading(true);
    try {
      const parameters = commandParameters ? JSON.parse(commandParameters) : {};
      
      // Mock command execution
      const affectedEAs = filterCriteria.groups.length * 2; // Mock calculation
      alert(`Command '${commandType}' executed on ${affectedEAs} EAs in selected groups (mock implementation)`);
    } catch (error) {
      console.error('Error executing command by groups:', error);
      alert('Failed to execute command');
    } finally {
      setLoading(false);
    }
  };

  const executeCommandByTags = async () => {
    if (Object.keys(filterCriteria.tags).length === 0) {
      alert('Please specify at least one tag filter');
      return;
    }

    setLoading(true);
    try {
      const parameters = commandParameters ? JSON.parse(commandParameters) : {};
      
      // Mock command execution
      const affectedEAs = Object.keys(filterCriteria.tags).length; // Mock calculation
      alert(`Command '${commandType}' executed on ${affectedEAs} EAs matching tag criteria (mock implementation)`);
    } catch (error) {
      console.error('Error executing command by tags:', error);
      alert('Failed to execute command');
    } finally {
      setLoading(false);
    }
  };

  const executeCommandByCriteria = async () => {
    setLoading(true);
    try {
      const parameters = commandParameters ? JSON.parse(commandParameters) : {};
      
      // Mock command execution
      const totalCriteria = filterCriteria.symbols.length + filterCriteria.strategies.length + filterCriteria.groups.length;
      const affectedEAs = Math.max(1, totalCriteria); // Mock calculation
      alert(`Command '${commandType}' executed on ${affectedEAs} EAs matching all criteria (mock implementation)`);
    } catch (error) {
      console.error('Error executing command by criteria:', error);
      alert('Failed to execute command');
    } finally {
      setLoading(false);
    }
  };

  // Helper functions
  const getUniqueSymbols = () => {
    return [...new Set(eas.map(ea => ea.symbol))];
  };

  const getUniqueStrategies = () => {
    return [...new Set(eas.map(ea => ea.strategy_tag))];
  };

  const getEAsByGroup = (groupId) => {
    // Mock implementation - return some EAs for demo
    const group = groups.find(g => g.id === groupId);
    if (!group) return [];
    
    // Return EAs that match the group type
    if (group.group_type === 'symbol') {
      const symbol = group.group_name.replace('Symbol_', '');
      return eas.filter(ea => ea.symbol === symbol);
    } else if (group.group_type === 'strategy') {
      const strategy = group.group_name.replace('Strategy_', '').replace('_', ' ');
      return eas.filter(ea => ea.strategy_tag === strategy);
    }
    
    return eas.slice(0, 2); // Mock: return first 2 EAs
  };

  const getEAsByTag = (tagName, tagValue = null) => {
    return eas.filter(ea => {
      const eaTags = tags[ea.id];
      if (!eaTags || !eaTags[tagName]) return false;
      if (tagValue === null) return true;
      return eaTags[tagName] === tagValue;
    });
  };

  return (
    <div className="ea-grouping-panel">
      <div className="panel-header">
        <h3>EA Grouping & Tagging System</h3>
        <div className="mock-notice" style={{color: '#ffa500', fontSize: '0.9em', fontStyle: 'italic'}}>
          
        </div>
        <div className="tab-buttons">
          <button 
            className={activeTab === 'groups' ? 'active' : ''}
            onClick={() => setActiveTab('groups')}
          >
            Groups
          </button>
          <button 
            className={activeTab === 'tags' ? 'active' : ''}
            onClick={() => setActiveTab('tags')}
          >
            Tags
          </button>
          <button 
            className={activeTab === 'commands' ? 'active' : ''}
            onClick={() => setActiveTab('commands')}
          >
            Mass Commands
          </button>
          <button 
            className={activeTab === 'stats' ? 'active' : ''}
            onClick={() => setActiveTab('stats')}
          >
            Statistics
          </button>
        </div>
      </div>

      {activeTab === 'groups' && (
        <div className="groups-tab">
          <div className="auto-grouping-section">
            <h4>Auto-Grouping</h4>
            <div className="auto-group-buttons">
              <button onClick={autoGroupBySymbol} disabled={loading}>
                Group by Symbol
              </button>
              <button onClick={autoGroupByStrategy} disabled={loading}>
                Group by Strategy
              </button>
              <button onClick={autoGroupByRiskLevel} disabled={loading}>
                Group by Risk Level
              </button>
            </div>
          </div>

          <div className="create-group-section">
            <h4>Create New Group</h4>
            <div className="create-group-form">
              <input
                type="text"
                placeholder="Group Name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
              />
              <select
                value={newGroupType}
                onChange={(e) => setNewGroupType(e.target.value)}
              >
                <option value="custom">Custom</option>
                <option value="symbol">Symbol</option>
                <option value="strategy">Strategy</option>
                <option value="risk_level">Risk Level</option>
              </select>
              <input
                type="text"
                placeholder="Description (optional)"
                value={newGroupDescription}
                onChange={(e) => setNewGroupDescription(e.target.value)}
              />
              <button onClick={createGroup} disabled={loading}>
                Create Group
              </button>
            </div>
          </div>

          <div className="groups-list">
            <h4>Existing Groups</h4>
            {groups.map(group => (
              <div key={group.id} className="group-item">
                <div className="group-header">
                  <span className="group-name">{group.group_name}</span>
                  <span className="group-type">{group.group_type}</span>
                  <span className="member-count">
                    {getEAsByGroup(group.id).length} members
                  </span>
                  <button 
                    className="delete-btn"
                    onClick={() => deleteGroup(group.id)}
                    disabled={loading}
                  >
                    Delete
                  </button>
                </div>
                {group.description && (
                  <div className="group-description">{group.description}</div>
                )}
                <div className="group-members">
                  {getEAsByGroup(group.id).map(ea => (
                    <div key={ea.id} className="member-item">
                      <span>{ea.magic_number} - {ea.symbol} ({ea.strategy_tag})</span>
                      <button 
                        className="remove-btn"
                        onClick={() => removeEAFromGroup(ea.id, group.id)}
                        disabled={loading}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'tags' && (
        <div className="tags-tab">
          <div className="add-tag-section">
            <h4>Add Tag to EA</h4>
            <div className="add-tag-form">
              <select
                value={selectedEAForTag || ''}
                onChange={(e) => setSelectedEAForTag(parseInt(e.target.value))}
              >
                <option value="">Select EA</option>
                {eas.map(ea => (
                  <option key={ea.id} value={ea.id}>
                    {ea.magic_number} - {ea.symbol} ({ea.strategy_tag})
                  </option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Tag Name"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
              />
              <input
                type="text"
                placeholder="Tag Value (optional)"
                value={newTagValue}
                onChange={(e) => setNewTagValue(e.target.value)}
              />
              <button onClick={addTag} disabled={loading}>
                Add Tag
              </button>
            </div>
          </div>

          <div className="eas-with-tags">
            <h4>EAs with Tags</h4>
            {eas.filter(ea => tags[ea.id] && Object.keys(tags[ea.id]).length > 0).map(ea => (
              <div key={ea.id} className="ea-tags-item">
                <div className="ea-info">
                  <strong>{ea.magic_number} - {ea.symbol} ({ea.strategy_tag})</strong>
                </div>
                <div className="ea-tags">
                  {Object.entries(tags[ea.id] || {}).map(([tagName, tagValue]) => (
                    <div key={tagName} className="tag-item">
                      <span className="tag-name">{tagName}</span>
                      {tagValue && <span className="tag-value">: {tagValue}</span>}
                      <button 
                        className="remove-tag-btn"
                        onClick={() => removeTag(ea.id, tagName)}
                        disabled={loading}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'commands' && (
        <div className="commands-tab">
          <div className="command-setup">
            <h4>Mass Command Execution</h4>
            <div className="command-form">
              <div className="command-type-section">
                <label>Command Type:</label>
                <select
                  value={commandType}
                  onChange={(e) => setCommandType(e.target.value)}
                >
                  <option value="pause">Pause</option>
                  <option value="resume">Resume</option>
                  <option value="adjust_risk">Adjust Risk</option>
                  <option value="close_positions">Close Positions</option>
                </select>
              </div>

              <div className="command-parameters-section">
                <label>Parameters (JSON):</label>
                <textarea
                  placeholder='{"new_risk_level": 1.5}'
                  value={commandParameters}
                  onChange={(e) => setCommandParameters(e.target.value)}
                />
              </div>

              <div className="filter-criteria-section">
                <h5>Filter Criteria</h5>
                
                <div className="filter-group">
                  <label>Symbols:</label>
                  <div className="checkbox-group">
                    {getUniqueSymbols().map(symbol => (
                      <label key={symbol}>
                        <input
                          type="checkbox"
                          checked={filterCriteria.symbols.includes(symbol)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFilterCriteria(prev => ({
                                ...prev,
                                symbols: [...prev.symbols, symbol]
                              }));
                            } else {
                              setFilterCriteria(prev => ({
                                ...prev,
                                symbols: prev.symbols.filter(s => s !== symbol)
                              }));
                            }
                          }}
                        />
                        {symbol}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="filter-group">
                  <label>Strategies:</label>
                  <div className="checkbox-group">
                    {getUniqueStrategies().map(strategy => (
                      <label key={strategy}>
                        <input
                          type="checkbox"
                          checked={filterCriteria.strategies.includes(strategy)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFilterCriteria(prev => ({
                                ...prev,
                                strategies: [...prev.strategies, strategy]
                              }));
                            } else {
                              setFilterCriteria(prev => ({
                                ...prev,
                                strategies: prev.strategies.filter(s => s !== strategy)
                              }));
                            }
                          }}
                        />
                        {strategy}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="filter-group">
                  <label>Groups:</label>
                  <div className="checkbox-group">
                    {groups.map(group => (
                      <label key={group.id}>
                        <input
                          type="checkbox"
                          checked={filterCriteria.groups.includes(group.group_name)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFilterCriteria(prev => ({
                                ...prev,
                                groups: [...prev.groups, group.group_name]
                              }));
                            } else {
                              setFilterCriteria(prev => ({
                                ...prev,
                                groups: prev.groups.filter(g => g !== group.group_name)
                              }));
                            }
                          }}
                        />
                        {group.group_name} ({group.group_type})
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="execute-buttons">
                <button 
                  onClick={executeCommandByGroups}
                  disabled={loading || filterCriteria.groups.length === 0}
                >
                  Execute by Groups
                </button>
                <button 
                  onClick={executeCommandByTags}
                  disabled={loading || Object.keys(filterCriteria.tags).length === 0}
                >
                  Execute by Tags
                </button>
                <button 
                  onClick={executeCommandByCriteria}
                  disabled={loading}
                >
                  Execute by All Criteria
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="stats-tab">
          <h4>Grouping System Statistics</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <label>Total EAs:</label>
              <span>{groupingStats.total_eas || 0}</span>
            </div>
            <div className="stat-item">
              <label>Total Groups:</label>
              <span>{groupingStats.total_groups || 0}</span>
            </div>
            <div className="stat-item">
              <label>Total Tags:</label>
              <span>{groupingStats.total_tags || 0}</span>
            </div>
            <div className="stat-item">
              <label>Total Memberships:</label>
              <span>{groupingStats.total_memberships || 0}</span>
            </div>
          </div>

          <div className="group-types-stats">
            <h5>Groups by Type</h5>
            {Object.entries(groupingStats.group_types || {}).map(([type, count]) => (
              <div key={type} className="stat-item">
                <label>{type}:</label>
                <span>{count}</span>
              </div>
            ))}
          </div>

          <div className="tag-usage-stats">
            <h5>Tag Usage</h5>
            {Object.entries(groupingStats.tag_usage || {}).map(([tag, count]) => (
              <div key={tag} className="stat-item">
                <label>{tag}:</label>
                <span>{count} EAs</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner">Loading...</div>
        </div>
      )}
    </div>
  );
};

export default EAGroupingPanel;