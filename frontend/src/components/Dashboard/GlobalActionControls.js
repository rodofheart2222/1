import React, { useState } from 'react';
import { Card, Button, Select, Space, Modal, message, Divider, Tag, Row, Col, Switch } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  ControlOutlined
} from '@ant-design/icons';
import '../../styles/liquid-glass-theme.css';
import apiService from '../../services/api';

const { Option } = Select;
const { confirm } = Modal;

const GlobalActionControls = ({ eaData = [], onCommandExecute }) => {
  const [selectedAction, setSelectedAction] = useState('');
  const [targetScope, setTargetScope] = useState('all');
  const [targetValue, setTargetValue] = useState('');
  const [executionMode, setExecutionMode] = useState('immediate'); // immediate, next_candle
  const [loading, setLoading] = useState(false);

  // Get unique values for targeting
  const symbols = [...new Set(eaData.map(ea => ea.symbol))];
  const strategies = [...new Set(eaData.map(ea => ea.strategy_tag))];

  const actionTypes = [
    {
      key: 'pause_all',
      label: 'Pause All EAs',
      icon: <PauseCircleOutlined />,
      color: 'orange',
      description: 'Pause all selected EAs from opening new positions'
    },
    {
      key: 'resume_all',
      label: 'Resume All EAs',
      icon: <PlayCircleOutlined />,
      color: 'green',
      description: 'Resume trading for all selected EAs'
    },
    {
      key: 'close_all_positions',
      label: 'Close All Positions',
      icon: <StopOutlined />,
      color: 'red',
      description: 'Close all open positions for selected EAs'
    },
    {
      key: 'emergency_stop',
      label: 'Emergency Stop',
      icon: <ExclamationCircleOutlined />,
      color: 'red',
      description: 'Immediately stop all trading activity'
    }
  ];

  const getTargetOptions = () => {
    const options = [
      { label: 'All EAs', value: 'all', count: eaData.length }
    ];

    // Add symbol-based targeting
    symbols.forEach(symbol => {
      const count = eaData.filter(ea => ea.symbol === symbol).length;
      options.push({
        label: `All ${symbol} EAs`,
        value: `symbol:${symbol}`,
        count
      });
    });

    // Add strategy-based targeting
    strategies.forEach(strategy => {
      const count = eaData.filter(ea => ea.strategy_tag === strategy).length;
      options.push({
        label: `All "${strategy}" EAs`,
        value: `strategy:${strategy}`,
        count
      });
    });

    // Add status-based targeting
    const activeCount = eaData.filter(ea => ea.open_positions > 0).length;
    const profitableCount = eaData.filter(ea => (ea.current_profit || 0) > 0).length;
    const losingCount = eaData.filter(ea => (ea.current_profit || 0) < 0).length;

    if (activeCount > 0) {
      options.push({
        label: 'Active EAs Only',
        value: 'status:active',
        count: activeCount
      });
    }

    if (profitableCount > 0) {
      options.push({
        label: 'Profitable EAs Only',
        value: 'status:profitable',
        count: profitableCount
      });
    }

    if (losingCount > 0) {
      options.push({
        label: 'Losing EAs Only',
        value: 'status:losing',
        count: losingCount
      });
    }

    return options;
  };

  const getAffectedEACount = () => {
    if (targetScope === 'all') return eaData.length;
    
    const [type, value] = targetScope.split(':');
    
    switch (type) {
      case 'symbol':
        return eaData.filter(ea => ea.symbol === value).length;
      case 'strategy':
        return eaData.filter(ea => ea.strategy_tag === value).length;
      case 'status':
        if (value === 'active') return eaData.filter(ea => ea.open_positions > 0).length;
        if (value === 'profitable') return eaData.filter(ea => (ea.current_profit || 0) > 0).length;
        if (value === 'losing') return eaData.filter(ea => (ea.current_profit || 0) < 0).length;
        break;
      default:
        return 0;
    }
    return 0;
  };

  const getAffectedEAs = () => {
    if (targetScope === 'all') return eaData;
    
    const [type, value] = targetScope.split(':');
    
    switch (type) {
      case 'symbol':
        return eaData.filter(ea => ea.symbol === value);
      case 'strategy':
        return eaData.filter(ea => ea.strategy_tag === value);
      case 'status':
        if (value === 'active') return eaData.filter(ea => ea.open_positions > 0);
        if (value === 'profitable') return eaData.filter(ea => (ea.current_profit || 0) > 0);
        if (value === 'losing') return eaData.filter(ea => (ea.current_profit || 0) < 0);
        break;
      default:
        return [];
    }
    return [];
  };

  const executeGlobalAction = () => {
    const selectedActionData = actionTypes.find(action => action.key === selectedAction);
    const affectedCount = getAffectedEACount();

    if (!selectedActionData || affectedCount === 0) {
      message.error('Please select a valid action and target');
      return;
    }

    const isHighRisk = selectedAction === 'emergency_stop' || selectedAction === 'close_all_positions';

    confirm({
      title: `Confirm ${selectedActionData.label}`,
      icon: isHighRisk ? <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} /> : <ControlOutlined />,
      content: (
        <div>
          <p><strong>Action:</strong> {selectedActionData.label}</p>
          <p><strong>Target:</strong> {getTargetOptions().find(opt => opt.value === targetScope)?.label}</p>
          <p><strong>Affected EAs:</strong> {affectedCount}</p>
          <p><strong>Execution:</strong> {executionMode === 'immediate' ? 'Immediate' : 'Next Candle Open'}</p>
          <Divider />
          <p style={{ color: isHighRisk ? '#ff4d4f' : '#666' }}>
            {selectedActionData.description}
          </p>
          {isHighRisk && (
            <p style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
              ️ This is a high-risk action that cannot be undone!
            </p>
          )}
        </div>
      ),
      okText: 'Execute',
      okType: isHighRisk ? 'danger' : 'primary',
      cancelText: 'Cancel',
      onOk: async () => {
        setLoading(true);
        try {
          // Get affected EAs
          const affectedEAs = getAffectedEAs();
          
          // Convert action key to command
          const commandMap = {
            'pause_all': 'pause',
            'resume_all': 'resume',
            'close_all_positions': 'close_positions',
            'emergency_stop': 'emergency_stop'
          };
          
          const command = commandMap[selectedAction];
          if (!command) {
            throw new Error(`Unknown action: ${selectedAction}`);
          }
          
          // Execute command immediately on each affected EA
          const results = [];
          for (const ea of affectedEAs) {
            try {
              await apiService.sendEACommand(ea.magic_number, {
                command: command,
                parameters: {
                  reason: `Global Action: ${selectedActionData.label}`,
                  scope: targetScope,
                  execution_mode: executionMode,
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
            message.success(`${selectedActionData.label} executed successfully on ${successful} EA(s)`);
          } else if (successful === 0) {
            message.error(`Failed to execute ${selectedActionData.label} on all ${failed} EA(s)`);
          } else {
            message.warning(`${selectedActionData.label} executed on ${successful} EA(s), failed on ${failed} EA(s)`);
          }
          
          // Also add to queue for tracking
          if (onCommandExecute) {
            const queueCommand = {
              type: 'global_action',
              action: selectedAction,
              command: command,
              targets: affectedEAs.map(ea => ea.magic_number),
              target_scope: targetScope,
              execution_mode: executionMode,
              affected_count: affectedCount,
              status: 'completed',
              timestamp: new Date().toISOString(),
              description: `${selectedActionData.label} on ${affectedCount} EA(s)`,
              results: results,
              parameters: {
                reason: `Global Action: ${selectedActionData.label}`,
                scope: targetScope,
                execution_mode: executionMode
              },
              affectedEAs: affectedEAs
            };
            await onCommandExecute(queueCommand);
          }
          
          // Reset form
          setSelectedAction('');
          setTargetScope('all');
          setTargetValue('');
          setExecutionMode('immediate');
          
        } catch (error) {
          message.error('Failed to execute command: ' + error.message);
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const targetOptions = getTargetOptions();
  const affectedCount = getAffectedEACount();
  const selectedActionData = actionTypes.find(action => action.key === selectedAction);

  return (
    <Card
      title={
        <Space>
          Global Action Controls
        </Space>
      }
      className="global-action-controls"
      size="small"
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* Action Selection */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Select Action:
          </div>
          <Select
            placeholder="Choose global action"
            style={{ width: '100%' }}
            value={selectedAction}
            onChange={setSelectedAction}
          >
            {actionTypes.map(action => (
              <Option key={action.key} value={action.key}>
                <Space>
                  {action.icon}
                  <span>{action.label}</span>
                </Space>
              </Option>
            ))}
          </Select>
          {selectedActionData && (
            <div style={{ 
              marginTop: 8, 
              padding: 8, 
              background: '#f5f5f5', 
              borderRadius: 4,
              fontSize: '11px',
              color: '#666'
            }}>
              {selectedActionData.description}
            </div>
          )}
        </div>

        {/* Target Selection */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Target EAs:
          </div>
          <Select
            placeholder="Select target EAs"
            style={{ width: '100%' }}
            value={targetScope}
            onChange={setTargetScope}
          >
            {targetOptions.map(option => (
              <Option key={option.value} value={option.value}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{option.label}</span>
                  <Tag size="small" color="blue">{option.count}</Tag>
                </div>
              </Option>
            ))}
          </Select>
        </div>

        {/* Execution Mode */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Execution Mode:
          </div>
          <Row gutter={8}>
            <Col span={12}>
              <Button
                type={executionMode === 'immediate' ? 'primary' : 'default'}
                size="small"
                icon={<ThunderboltOutlined />}
                onClick={() => setExecutionMode('immediate')}
                style={{ width: '100%' }}
              >
                Immediate
              </Button>
            </Col>
            <Col span={12}>
              <Button
                type={executionMode === 'next_candle' ? 'primary' : 'default'}
                size="small"
                icon={<ClockCircleOutlined />}
                onClick={() => setExecutionMode('next_candle')}
                style={{ width: '100%' }}
              >
                Next Candle
              </Button>
            </Col>
          </Row>
        </div>

        {/* Summary */}
        {selectedAction && (
          <div style={{ 
            padding: 12, 
            background: selectedActionData?.color === 'red' ? '#fff2f0' : '#f6ffed', 
            border: `1px solid ${selectedActionData?.color === 'red' ? '#ffccc7' : '#d9f7be'}`,
            borderRadius: 4 
          }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: 4 }}>
              Action Summary:
            </div>
            <div style={{ fontSize: '11px', color: '#666' }}>
              <div>Action: <strong>{selectedActionData?.label}</strong></div>
              <div>Target: <strong>{targetOptions.find(opt => opt.value === targetScope)?.label}</strong></div>
              <div>Affected EAs: <strong style={{ color: selectedActionData?.color === 'red' ? '#ff4d4f' : '#52c41a' }}>
                {affectedCount}
              </strong></div>
              <div>Execution: <strong>{executionMode === 'immediate' ? 'Immediate' : 'Next Candle Open'}</strong></div>
            </div>
          </div>
        )}

        {/* Execute Button */}
        <button
          className={`liquid-glass-button liquid-glass-button-medium ${selectedActionData?.color === 'red' ? 'liquid-glass-button-primary' : 'liquid-glass-button-primary'} ${loading ? 'liquid-glass-loading' : ''}`}
          onClick={executeGlobalAction}
          disabled={!selectedAction || affectedCount === 0}
          style={{ 
            width: '100%',
            '--lg-action': selectedActionData?.color === 'red' ? '#F44336' : '#52c41a',
            border: 'none',
            cursor: !selectedAction || affectedCount === 0 ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          {selectedActionData?.icon}
          Execute {selectedActionData?.label || 'Action'}
        </button>

        {/* Quick Actions */}
        <Divider style={{ margin: '12px 0' }}>Quick Actions</Divider>
        <Row gutter={[8, 8]}>
          <Col span={12}>
            <Button
              size="small"
              icon={<PauseCircleOutlined />}
              onClick={() => {
                setSelectedAction('pause_all');
                setTargetScope('all');
                setExecutionMode('immediate');
              }}
              style={{ width: '100%' }}
            >
              Pause All
            </Button>
          </Col>
          <Col span={12}>
            <Button
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => {
                setSelectedAction('resume_all');
                setTargetScope('all');
                setExecutionMode('immediate');
              }}
              style={{ width: '100%' }}
            >
              Resume All
            </Button>
          </Col>
        </Row>
      </Space>
    </Card>
  );
};

export default GlobalActionControls;