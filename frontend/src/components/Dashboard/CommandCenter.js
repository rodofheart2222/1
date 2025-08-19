import React, { useState } from 'react';
import { Card, Button, Select, Input, Space, Modal, message, Tag } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined,
  SettingOutlined,
  SendOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import '../../styles/liquid-glass-theme.css';
import apiService from '../../services/api';

const { Option } = Select;
const { TextArea } = Input;

const CommandCenter = ({ eaData = [], onCommandExecute }) => {
  const [selectedCommand, setSelectedCommand] = useState('');
  const [selectedEAs, setSelectedEAs] = useState([]);
  const [commandParams, setCommandParams] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  // Get unique values for EA selection with null safety
  const symbols = [...new Set((eaData || []).map(ea => ea?.symbol).filter(Boolean))];
  const strategies = [...new Set((eaData || []).map(ea => ea?.strategy_tag).filter(Boolean))];

  const commandTypes = [
    { value: 'pause', label: 'Pause EAs', icon: <PauseCircleOutlined /> },
    { value: 'resume', label: 'Resume EAs', icon: <PlayCircleOutlined /> },
    { value: 'close_positions', label: 'Close Positions', icon: <StopOutlined /> },
    { value: 'adjust_risk', label: 'Adjust Risk', icon: <SettingOutlined /> }
  ];

  const handleCommandSelect = (command) => {
    setSelectedCommand(command);
    setCommandParams('');
  };

  const handleEASelection = (values) => {
    setSelectedEAs(values);
  };

  const getEASelectionOptions = () => {
    const options = [];
    
    // Individual EAs
    (eaData || []).forEach(ea => {
      if (ea?.symbol && ea?.strategy_tag && ea?.magic_number) {
        options.push({
          label: `${ea.symbol} - ${ea.strategy_tag} (#${ea.magic_number})`,
          value: `ea_${ea.magic_number}`
        });
      }
    });
    
    // Symbol groups
    symbols.forEach(symbol => {
      if (symbol) {
        options.push({
          label: `All ${symbol} EAs`,
          value: `symbol_${symbol}`
        });
      }
    });
    
    // Strategy groups
    strategies.forEach(strategy => {
      if (strategy) {
        options.push({
          label: `All ${strategy} EAs`,
          value: `strategy_${strategy}`
        });
      }
    });
    
    // All EAs
    if ((eaData || []).length > 0) {
      options.push({
        label: 'All EAs',
        value: 'all'
      });
    }
    
    return options;
  };

  const getCommandParamsPlaceholder = () => {
    switch (selectedCommand) {
      case 'adjust_risk':
        return 'Enter risk parameters (e.g., {"risk_percent": 2.0, "max_positions": 3})';
      case 'close_positions':
        return 'Enter close parameters (e.g., {"close_type": "all"} or {"close_type": "profitable"})';
      default:
        return 'Enter command parameters (JSON format)';
    }
  };

  const validateCommand = () => {
    if (!selectedCommand) {
      message.error('Please select a command type');
      return false;
    }
    
    if (selectedEAs.length === 0) {
      message.error('Please select at least one EA or group');
      return false;
    }
    
    if (commandParams && selectedCommand !== 'pause' && selectedCommand !== 'resume') {
      try {
        JSON.parse(commandParams);
      } catch (e) {
        message.error('Invalid JSON format in parameters');
        return false;
      }
    }
    
    return true;
  };

  const executeCommandNow = async () => {
    if (!validateCommand()) return;
    
    setLoading(true);
    
    try {
      const parameters = commandParams ? JSON.parse(commandParams) : {};
      
      // Get target EAs with full data
      const targetEAs = selectedEAs.map(eaId => 
        eaData.find(ea => ea.magic_number === eaId)
      ).filter(Boolean);
      
      if (targetEAs.length === 0) {
        message.error('No valid EAs selected');
        return;
      }
      
      // Send command immediately to each selected EA
      const results = [];
      for (const ea of targetEAs) {
        try {
          await apiService.sendEACommand(ea.magic_number, {
            command: selectedCommand,
            parameters: {
              ...parameters,
              reason: `Command Center: ${selectedCommand}`,
              timestamp: new Date().toISOString()
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
        message.success(`Command "${selectedCommand}" executed successfully on ${successful} EA(s)`);
      } else if (successful === 0) {
        message.error(`Failed to execute command on all ${failed} EA(s)`);
      } else {
        message.warning(`Command executed on ${successful} EA(s), failed on ${failed} EA(s)`);
      }
      
      // Reset form
      setSelectedCommand('');
      setSelectedEAs([]);
      setCommandParams('');
      setModalVisible(false);
      
    } catch (error) {
      message.error('Failed to execute command: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const queueCommand = async () => {
    if (!validateCommand()) return;
    
    try {
      const parameters = commandParams ? JSON.parse(commandParams) : {};
      
      // Get target EAs with full data
      const targetEAs = selectedEAs.map(eaId => 
        eaData.find(ea => ea.magic_number === eaId)
      ).filter(Boolean);
      
      if (targetEAs.length === 0) {
        message.error('No valid EAs selected');
        return;
      }
      
      // Queue command for execution in Action Queue
      if (onCommandExecute) {
        const queueCommand = {
          type: 'batch_command',
          command: selectedCommand,
          targets: targetEAs.map(ea => ea.magic_number),
          status: 'pending',
          timestamp: new Date().toISOString(),
          description: `${selectedCommand} on ${targetEAs.length} EA(s)`,
          parameters: {
            ...parameters,
            reason: `Command Center: ${selectedCommand}`,
            timestamp: new Date().toISOString()
          },
          // Include full EA data for UUID targeting
          affectedEAs: targetEAs
        };
        
        await onCommandExecute(queueCommand);
        message.success(`Command "${selectedCommand}" queued for ${targetEAs.length} EA(s). Check Action Queue to execute.`);
      } else {
        message.error('Command queue not available');
      }
      
      // Reset form
      setSelectedCommand('');
      setSelectedEAs([]);
      setCommandParams('');
      
    } catch (error) {
      message.error('Failed to queue command: ' + error.message);
    }
  };

  const showConfirmModal = () => {
    if (!validateCommand()) return;
    setModalVisible(true);
  };

  return (
    <Card
      title="Command Center"
      size="small"
      className="command-center glass-card"
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* Command Type Selection */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Command Type:
          </div>
          <Select
            placeholder="Select command"
            style={{ width: '100%' }}
            value={selectedCommand}
            onChange={handleCommandSelect}
          >
            {commandTypes.map(cmd => (
              <Option key={cmd.value} value={cmd.value}>
                {cmd.icon} {cmd.label}
              </Option>
            ))}
          </Select>
        </div>

        {/* EA Selection */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Target EAs:
          </div>
          <Select
            mode="multiple"
            placeholder="Select EAs or groups"
            style={{ width: '100%' }}
            value={selectedEAs}
            onChange={handleEASelection}
            maxTagCount={2}
          >
            {getEASelectionOptions().map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </div>

        {/* Command Parameters */}
        {selectedCommand && selectedCommand !== 'pause' && selectedCommand !== 'resume' && (
          <div>
            <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
              Parameters:
            </div>
            <TextArea
              placeholder={getCommandParamsPlaceholder()}
              value={commandParams}
              onChange={(e) => setCommandParams(e.target.value)}
              rows={3}
              style={{ fontSize: '11px' }}
            />
          </div>
        )}

        {/* Execute Button */}
        {/* Command Execution Buttons */}
        <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
          <button
            className="liquid-glass-button liquid-glass-button-primary liquid-glass-button-medium"
            onClick={showConfirmModal}
            disabled={!selectedCommand || selectedEAs.length === 0}
            style={{ 
              flex: 1,
              border: 'none',
              cursor: !selectedCommand || selectedEAs.length === 0 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <SendOutlined />
            Execute Now
          </button>
          
          <button
            className="liquid-glass-button liquid-glass-button-secondary liquid-glass-button-medium"
            onClick={queueCommand}
            disabled={!selectedCommand || selectedEAs.length === 0}
            style={{ 
              flex: 1,
              border: 'none',
              cursor: !selectedCommand || selectedEAs.length === 0 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <ClockCircleOutlined />
            Add to Queue
          </button>
        </div>

        {/* Active EAs Summary */}
        <div style={{ 
          marginTop: 16, 
          padding: 8, 
          background: 'color-mix(in srgb, var(--lg-glass) 1%, transparent)', 
          backdropFilter: 'blur(6px) saturate(var(--lg-saturation))',
          WebkitBackdropFilter: 'blur(6px) saturate(var(--lg-saturation))',
          border: '1px solid color-mix(in srgb, var(--lg-light) calc(var(--lg-glass-reflex-light) * 6%), transparent)',
          borderRadius: 4,
          boxShadow: 'inset 0 0 0 1px color-mix(in srgb, var(--lg-light) calc(var(--lg-glass-reflex-light) * 3%), transparent), 0 2px 8px color-mix(in srgb, var(--lg-dark) calc(var(--lg-glass-reflex-dark) * 8%), transparent)'
        }}>
          <div style={{ fontSize: '11px', color: '#a6a6a6', marginBottom: 4 }}>
            Connected EAs:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(eaData || []).slice(0, 6).map(ea => (
              <Tag key={ea?.magic_number || Math.random()} size="small" color={(ea?.open_positions || 0) > 0 ? 'green' : 'default'}>
                {ea?.symbol || 'Unknown'}
              </Tag>
            ))}
            {(eaData || []).length > 6 && (
              <Tag size="small">+{(eaData || []).length - 6} more</Tag>
            )}
          </div>
        </div>
      </Space>

      {/* Confirmation Modal */}
      <Modal
        title="Confirm Command Execution"
        open={modalVisible}
        onOk={executeCommandNow}
        onCancel={() => setModalVisible(false)}
        confirmLoading={loading}
        okText="Execute"
        cancelText="Cancel"
        className="glass-modal"
      >
        <div>
          <p><strong>Command:</strong> {selectedCommand}</p>
          <p><strong>Targets:</strong> {selectedEAs.length} EA(s)/Group(s)</p>
          {commandParams && (
            <p><strong>Parameters:</strong></p>
          )}
          {commandParams && (
            <pre style={{ 
              background: 'color-mix(in srgb, var(--lg-glass) 1%, transparent)', 
              backdropFilter: 'blur(6px) saturate(var(--lg-saturation))',
              WebkitBackdropFilter: 'blur(6px) saturate(var(--lg-saturation))',
              border: '1px solid color-mix(in srgb, var(--lg-light) calc(var(--lg-glass-reflex-light) * 6%), transparent)',
              padding: 8, 
              borderRadius: 4,
              fontSize: '11px',
              whiteSpace: 'pre-wrap',
              color: 'var(--lg-content)',
              boxShadow: 'inset 0 0 0 1px color-mix(in srgb, var(--lg-light) calc(var(--lg-glass-reflex-light) * 3%), transparent), 0 2px 8px color-mix(in srgb, var(--lg-dark) calc(var(--lg-glass-reflex-dark) * 8%), transparent)'
            }}>
              {commandParams}
            </pre>
          )}
          <p style={{ color: '#fa8c16', fontSize: '12px' }}>
            ️ This action will be sent to all selected EAs immediately.
          </p>
        </div>
      </Modal>
    </Card>
  );
};

export default CommandCenter;