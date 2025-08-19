import React, { useState, useEffect, useContext } from 'react';
import { useDashboard } from '../../context/DashboardContext';
import apiService from '../../services/api';
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
    // Initialize with real EA data
    if (eas && eas.length > 0) {
      // Auto-create groups based on existing EA data
      const symbolGroups = [...new Set(eas.map(ea => ea.symbol))].map(symbol => ({
        id: `symbol_${symbol}`,
        group_name: `${symbol} Pairs`,
        group_type: 'symbol', 
        description: `All EAs trading ${symbol}`,
        filter_value: symbol
      }));
      
      const strategyGroups = [...new Set(eas.map(ea => ea.strategy_tag))].filter(Boolean).map(strategy => ({
        id: `strategy_${strategy}`,
        group_name: `${strategy} Strategy`,
        group_type: 'strategy',
        description: `All EAs using ${strategy} strategy`,
        filter_value: strategy
      }));
      
      const allGroups = [...symbolGroups, ...strategyGroups];
      setGroups(allGroups);
      
      setGroupingStats({
        total_eas: eas.length,
        total_groups: allGroups.length,
        total_tags: Object.keys(tags).length,
        total_memberships: calculateTotalMemberships(allGroups),
        group_types: { 
          symbol: symbolGroups.length, 
          strategy: strategyGroups.length 
        },
        tag_usage: calculateTagUsage()
      });
    }
  }, [eas, tags]);

  const calculateTotalMemberships = (groupList) => {
    return groupList.reduce((total, group) => {
      return total + getEAsByGroup(group.id).length;
    }, 0);
  };

  const calculateTagUsage = () => {
    const tagCounts = {};
    Object.values(tags).forEach(eaTags => {
      Object.keys(eaTags).forEach(tagName => {
        tagCounts[tagName] = (tagCounts[tagName] || 0) + 1;
      });
    });
    return tagCounts;
  };

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
      
      alert('Group created successfully');
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
      alert('Group deleted successfully');
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
      alert('EA added to group successfully');
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
      alert('EA removed from group successfully');
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
      alert(`Auto-grouped by symbol: created ${newGroups.length} groups`);
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
      alert(`Auto-grouped by strategy: created ${newGroups.length} groups`);
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
      alert(`Auto-grouped by risk level: created ${newGroups.length} groups`);
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
      alert('Tag added successfully');
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
      alert('Tag removed successfully');
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
      
      // Get all EAs from selected groups
      const affectedEAs = [];
      for (const groupId of filterCriteria.groups) {
        const groupEAs = getEAsByGroup(groupId);
        affectedEAs.push(...groupEAs);
      }
      
      // Remove duplicates (EA might be in multiple groups)
      const uniqueEAs = affectedEAs.filter((ea, index, self) => 
        index === self.findIndex(e => e.magic_number === ea.magic_number)
      );
      
      if (uniqueEAs.length === 0) {
        alert('No EAs found in selected groups');
        return;
      }
      
      // Execute command on each EA
      const results = [];
      for (const ea of uniqueEAs) {
        try {
          await apiService.sendEACommand(ea.magic_number, {
            command: commandType,
            parameters: {
              reason: `Group Action: ${commandType}`,
              source: 'EA Grouping Panel',
              timestamp: new Date().toISOString(),
              ...parameters
            },
            instance_uuid: ea.instance_uuid
          });
          results.push({ ea: ea.magic_number, status: 'success' });
        } catch (error) {
          console.error(`Failed to send command to EA ${ea.magic_number}:`, error);
          results.push({ ea: ea.magic_number, status: 'failed', error: error.message });
        }
      }
      
      // Report results
      const successful = results.filter(r => r.status === 'success').length;
      const failed = results.filter(r => r.status === 'failed').length;
      
      if (failed === 0) {
        alert(`Command '${commandType}' executed successfully on ${successful} EAs from selected groups`);
      } else if (successful === 0) {
        alert(`Failed to execute command on all ${failed} EAs`);
      } else {
        alert(`Command executed on ${successful} EAs, failed on ${failed} EAs`);
      }
      
    } catch (error) {
      console.error('Error executing command by groups:', error);
      alert('Failed to execute command: ' + error.message);
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
      
      // Get all EAs matching tag criteria
      const affectedEAs = [];
      for (const [tagName, tagValue] of Object.entries(filterCriteria.tags)) {
        const taggedEAs = getEAsByTag(tagName, tagValue);
        affectedEAs.push(...taggedEAs);
      }
      
      // Remove duplicates
      const uniqueEAs = affectedEAs.filter((ea, index, self) => 
        index === self.findIndex(e => e.magic_number === ea.magic_number)
      );
      
      if (uniqueEAs.length === 0) {
        alert('No EAs found matching tag criteria');
        return;
      }
      
      // Execute command on each EA
      const results = [];
      for (const ea of uniqueEAs) {
        try {
          await apiService.sendEACommand(ea.magic_number, {
            command: commandType,
            parameters: {
              reason: `Tag Action: ${commandType}`,
              source: 'EA Grouping Panel',
              timestamp: new Date().toISOString(),
              ...parameters
            },
            instance_uuid: ea.instance_uuid
          });
          results.push({ ea: ea.magic_number, status: 'success' });
        } catch (error) {
          console.error(`Failed to send command to EA ${ea.magic_number}:`, error);
          results.push({ ea: ea.magic_number, status: 'failed', error: error.message });
        }
      }
      
      // Report results
      const successful = results.filter(r => r.status === 'success').length;
      const failed = results.filter(r => r.status === 'failed').length;
      
      if (failed === 0) {
        alert(`Command '${commandType}' executed successfully on ${successful} EAs matching tag criteria`);
      } else if (successful === 0) {
        alert(`Failed to execute command on all ${failed} EAs`);
      } else {
        alert(`Command executed on ${successful} EAs, failed on ${failed} EAs`);
      }
      
    } catch (error) {
      console.error('Error executing command by tags:', error);
      alert('Failed to execute command: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const executeCommandByCriteria = async () => {
    setLoading(true);
    try {
      const parameters = commandParameters ? JSON.parse(commandParameters) : {};
      
      // Get EAs matching all criteria (AND operation)
      let affectedEAs = [...eas];
      
      // Filter by symbols if specified
      if (filterCriteria.symbols.length > 0) {
        affectedEAs = affectedEAs.filter(ea => filterCriteria.symbols.includes(ea.symbol));
      }
      
      // Filter by strategies if specified
      if (filterCriteria.strategies.length > 0) {
        affectedEAs = affectedEAs.filter(ea => filterCriteria.strategies.includes(ea.strategy_tag));
      }
      
      // Filter by groups if specified
      if (filterCriteria.groups.length > 0) {
        const groupEAs = [];
        for (const groupId of filterCriteria.groups) {
          groupEAs.push(...getEAsByGroup(groupId));
        }
        const groupMagicNumbers = [...new Set(groupEAs.map(ea => ea.magic_number))];
        affectedEAs = affectedEAs.filter(ea => groupMagicNumbers.includes(ea.magic_number));
      }
      
      // Filter by tags if specified
      if (Object.keys(filterCriteria.tags).length > 0) {
        affectedEAs = affectedEAs.filter(ea => {
          const eaTags = tags[ea.magic_number];
          if (!eaTags) return false;
          
          // Check if EA matches all tag criteria
          return Object.entries(filterCriteria.tags).every(([tagName, tagValue]) => {
            return eaTags[tagName] === tagValue;
          });
        });
      }
      
      if (affectedEAs.length === 0) {
        alert('No EAs found matching the specified criteria');
        return;
      }
      
      // Execute command on each EA
      const results = [];
      for (const ea of affectedEAs) {
        try {
          await apiService.sendEACommand(ea.magic_number, {
            command: commandType,
            parameters: {
              reason: `Criteria Action: ${commandType}`,
              source: 'EA Grouping Panel',
              timestamp: new Date().toISOString(),
              ...parameters
            },
            instance_uuid: ea.instance_uuid
          });
          results.push({ ea: ea.magic_number, status: 'success' });
        } catch (error) {
          console.error(`Failed to send command to EA ${ea.magic_number}:`, error);
          results.push({ ea: ea.magic_number, status: 'failed', error: error.message });
        }
      }
      
      // Report results
      const successful = results.filter(r => r.status === 'success').length;
      const failed = results.filter(r => r.status === 'failed').length;
      
      if (failed === 0) {
        alert(`Command '${commandType}' executed successfully on ${successful} EAs matching criteria`);
      } else if (successful === 0) {
        alert(`Failed to execute command on all ${failed} EAs`);
      } else {
        alert(`Command executed on ${successful} EAs, failed on ${failed} EAs`);
      }
      
    } catch (error) {
      console.error('Error executing command by criteria:', error);
      alert('Failed to execute command: ' + error.message);
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
    const group = groups.find(g => g.id === groupId);
    if (!group) return [];
    
    // Return EAs that match the group type and filter value
    if (group.group_type === 'symbol') {
      return eas.filter(ea => ea.symbol === group.filter_value);
    } else if (group.group_type === 'strategy') {
      return eas.filter(ea => ea.strategy_tag === group.filter_value);
    } else if (group.group_type === 'risk') {
      return eas.filter(ea => (ea.risk_config || 'default') === group.filter_value);
    } else if (group.group_type === 'custom') {
      // For custom groups, check if EAs are explicitly assigned
      // This would come from backend in real implementation
      return eas.filter(ea => group.ea_ids && group.ea_ids.includes(ea.magic_number));
    }
    
    return [];
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