import React, { useState } from 'react';
import { Card, Button, Select, Input, Space, Modal, message, Tag } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined,
  SettingOutlined,
  SendOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;

const CommandCenter = ({ eaData = [] }) => {
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

  const executeCommand = async () => {
    if (!validateCommand()) return;
    
    setLoading(true);
    
    try {
      const command = {
        type: selectedCommand,
        targets: selectedEAs,
        parameters: commandParams ? JSON.parse(commandParams) : {},
        timestamp: new Date().toISOString()
      };
      
      // Here we would send the command to the backend
      // For now, we'll simulate the command execution
      console.log('Executing command:', command);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      message.success(`Command "${selectedCommand}" sent successfully to ${selectedEAs.length} target(s)`);
      
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
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={showConfirmModal}
          disabled={!selectedCommand || selectedEAs.length === 0}
          style={{ width: '100%' }}
        >
          Execute Command
        </Button>

        {/* Active EAs Summary */}
        <div style={{ marginTop: 16, padding: 8, background: '#262626', borderRadius: 4 }}>
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
        onOk={executeCommand}
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
              background: '#262626', 
              padding: 8, 
              borderRadius: 4,
              fontSize: '11px',
              whiteSpace: 'pre-wrap',
              color: '#e0e0e0'
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