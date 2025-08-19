import React, { useState } from 'react';
import { Card, Button, Select, InputNumber, Space, Modal, message, Divider, Tag, Row, Col, Slider, Switch } from 'antd';
import { 
  SettingOutlined, 
  DollarOutlined, 
  PercentageOutlined,
  ExclamationCircleOutlined,
  SaveOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import apiService from '../../services/api';

const { Option } = Select;
const { confirm } = Modal;

const RiskAdjustmentInterface = ({ eaData = [], onRiskAdjust, viewMode = 'summary' }) => {
  const [adjustmentType, setAdjustmentType] = useState('risk_percent');
  const [targetScope, setTargetScope] = useState('all');
  const [adjustmentValue, setAdjustmentValue] = useState(2.0);
  const [adjustmentMode, setAdjustmentMode] = useState('absolute'); // absolute, relative
  const [applyImmediately, setApplyImmediately] = useState(true);
  const [loading, setLoading] = useState(false);

  // Get unique values for targeting
  const symbols = [...new Set(eaData.map(ea => ea.symbol))];
  const strategies = [...new Set(eaData.map(ea => ea.strategy_tag))];
  const riskLevels = [...new Set(eaData.map(ea => ea.risk_config || 'default'))];

  const adjustmentTypes = [
    {
      key: 'risk_percent',
      label: 'Risk Percentage',
      icon: <PercentageOutlined />,
      unit: '%',
      min: 0.1,
      max: 10.0,
      step: 0.1,
      description: 'Adjust risk percentage per trade'
    },
    {
      key: 'lot_size',
      label: 'Lot Size',
      icon: <DollarOutlined />,
      unit: 'lots',
      min: 0.01,
      max: 10.0,
      step: 0.01,
      description: 'Adjust fixed lot size for trades'
    },
    {
      key: 'max_positions',
      label: 'Max Positions',
      icon: <SettingOutlined />,
      unit: 'positions',
      min: 1,
      max: 20,
      step: 1,
      description: 'Maximum concurrent positions per EA'
    },
    {
      key: 'stop_loss_pips',
      label: 'Stop Loss (Pips)',
      icon: <ExclamationCircleOutlined />,
      unit: 'pips',
      min: 5,
      max: 500,
      step: 5,
      description: 'Default stop loss in pips'
    },
    {
      key: 'take_profit_pips',
      label: 'Take Profit (Pips)',
      icon: <DollarOutlined />,
      unit: 'pips',
      min: 5,
      max: 1000,
      step: 5,
      description: 'Default take profit in pips'
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

    // Add risk level targeting
    riskLevels.forEach(level => {
      const count = eaData.filter(ea => (ea.risk_config || 'default') === level).length;
      options.push({
        label: `Risk Level: ${level}`,
        value: `risk:${level}`,
        count
      });
    });

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
      case 'risk':
        return eaData.filter(ea => (ea.risk_config || 'default') === value).length;
      default:
        return 0;
    }
  };

  const getAffectedEAs = () => {
    if (targetScope === 'all') return eaData;
    
    const [type, value] = targetScope.split(':');
    
    switch (type) {
      case 'symbol':
        return eaData.filter(ea => ea.symbol === value);
      case 'strategy':
        return eaData.filter(ea => ea.strategy_tag === value);
      case 'risk':
        return eaData.filter(ea => (ea.risk_config || 'default') === value);
      default:
        return [];
    }
  };

  const getCurrentValues = () => {
    if (targetScope === 'all') {
      // Calculate average for all EAs
      const values = eaData.map(ea => ea[adjustmentType] || 0);
      const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
      return { min: Math.min(...values), max: Math.max(...values), avg };
    }
    
    const [type, value] = targetScope.split(':');
    let filteredEAs = [];
    
    switch (type) {
      case 'symbol':
        filteredEAs = eaData.filter(ea => ea.symbol === value);
        break;
      case 'strategy':
        filteredEAs = eaData.filter(ea => ea.strategy_tag === value);
        break;
      case 'risk':
        filteredEAs = eaData.filter(ea => (ea.risk_config || 'default') === value);
        break;
    }
    
    if (filteredEAs.length === 0) return { min: 0, max: 0, avg: 0 };
    
    const values = filteredEAs.map(ea => ea[adjustmentType] || 0);
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
    return { min: Math.min(...values), max: Math.max(...values), avg };
  };

  const executeRiskAdjustment = () => {
    const selectedType = adjustmentTypes.find(type => type.key === adjustmentType);
    const affectedCount = getAffectedEACount();
    const currentValues = getCurrentValues();

    if (!selectedType || affectedCount === 0) {
      message.error('Please select a valid adjustment type and target');
      return;
    }

    const finalValue = adjustmentMode === 'relative' 
      ? currentValues.avg + adjustmentValue 
      : adjustmentValue;

    confirm({
      title: `Confirm Risk Adjustment`,
      icon: <SettingOutlined />,
      content: (
        <div>
          <p><strong>Adjustment Type:</strong> {selectedType.label}</p>
          <p><strong>Target:</strong> {getTargetOptions().find(opt => opt.value === targetScope)?.label}</p>
          <p><strong>Affected EAs:</strong> {affectedCount}</p>
          <p><strong>Current Average:</strong> {currentValues.avg.toFixed(2)} {selectedType.unit}</p>
          <p><strong>New Value:</strong> {finalValue.toFixed(2)} {selectedType.unit}</p>
          <p><strong>Mode:</strong> {adjustmentMode === 'absolute' ? 'Set to value' : 'Adjust by value'}</p>
          <p><strong>Apply:</strong> {applyImmediately ? 'Immediately' : 'Next trade'}</p>
          <Divider />
          <p style={{ color: '#a6a6a6' }}>
            {selectedType.description}
          </p>
          <p style={{ color: '#fa8c16', fontSize: '12px' }}>
            ️ Risk adjustments will affect all future trades for selected EAs.
          </p>
        </div>
      ),
      okText: 'Apply Adjustment',
      okType: 'primary',
      cancelText: 'Cancel',
      onOk: async () => {
        setLoading(true);
        try {
          // Get affected EAs
          const affectedEAs = getAffectedEAs();
          
          // Execute risk adjustment immediately on each affected EA
          const results = [];
          for (const ea of affectedEAs) {
            try {
              await apiService.sendEACommand(ea.magic_number, {
                command: 'adjust_risk',
                parameters: {
                  adjustment_type: adjustmentType,
                  adjustment_value: adjustmentValue,
                  adjustment_mode: adjustmentMode,
                  final_value: finalValue,
                  apply_immediately: applyImmediately,
                  reason: `Risk Adjustment: ${selectedType.label}`,
                  timestamp: new Date().toISOString()
                },
                instance_uuid: ea.instance_uuid
              });
              results.push({ ea: ea.magic_number, status: 'success' });
            } catch (error) {
              console.error(`Failed to send risk adjustment to EA ${ea.magic_number}:`, error);
              results.push({ ea: ea.magic_number, status: 'failed', error: error.message });
            }
          }
          
          // Report results
          const successful = results.filter(r => r.status === 'success').length;
          const failed = results.filter(r => r.status === 'failed').length;
          
          if (failed === 0) {
            message.success(`Risk adjustment executed successfully on ${successful} EA(s)`);
          } else if (successful === 0) {
            message.error(`Failed to execute risk adjustment on all ${failed} EA(s)`);
          } else {
            message.warning(`Risk adjustment executed on ${successful} EA(s), failed on ${failed} EA(s)`);
          }
          
          // Also add to queue for tracking
          if (onRiskAdjust) {
            const command = {
              type: 'risk_adjustment',
              adjustment_type: adjustmentType,
              target_scope: targetScope,
              adjustment_value: adjustmentValue,
              adjustment_mode: adjustmentMode,
              final_value: finalValue,
              apply_immediately: applyImmediately,
              affected_count: affectedCount,
              status: 'completed',
              results: results,
              timestamp: new Date().toISOString()
            };
            await onRiskAdjust(command);
          }
          
        } catch (error) {
          message.error('Failed to apply risk adjustment: ' + error.message);
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const resetToDefaults = () => {
    setAdjustmentType('risk_percent');
    setTargetScope('all');
    setAdjustmentValue(2.0);
    setAdjustmentMode('absolute');
    setApplyImmediately(true);
  };

  const targetOptions = getTargetOptions();
  const affectedCount = getAffectedEACount();
  const selectedType = adjustmentTypes.find(type => type.key === adjustmentType);
  const currentValues = getCurrentValues();

  return (
    <Card
      title={
        <Space>
          Risk Adjustment Interface
        </Space>
      }
      className="risk-adjustment-interface glass-card"
      size="small"
      extra={
        <Button 
          size="small" 
          icon={<ReloadOutlined />}
          onClick={resetToDefaults}
          className="glass-button"
        >
          Reset
        </Button>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* Adjustment Type Selection */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Risk Parameter:
          </div>
          <Select
            placeholder="Select parameter to adjust"
            style={{ width: '100%' }}
            value={adjustmentType}
            onChange={setAdjustmentType}
          >
            {adjustmentTypes.map(type => (
              <Option key={type.key} value={type.key}>
                <Space>
                  {type.icon}
                  <span>{type.label}</span>
                </Space>
              </Option>
            ))}
          </Select>
          {selectedType && (
            <div style={{ 
              marginTop: 8, 
              padding: 8, 
              background: '#262626', 
              borderRadius: 4,
              fontSize: '11px',
              color: '#a6a6a6'
            }}>
              {selectedType.description}
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

        {/* Current Values Display */}
        {affectedCount > 0 && (
          <div style={{ 
            padding: 8, 
            background: '#1f1f1f', 
            border: '1px solid #404040',
            borderRadius: 4 
          }}>
            <div style={{ fontSize: '11px', fontWeight: 'bold', marginBottom: 4, color: '#e0e0e0' }}>
              Current Values:
            </div>
            <Row gutter={8}>
              <Col span={8}>
                <div style={{ fontSize: '10px', color: '#a6a6a6' }}>Min</div>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#e0e0e0' }}>
                  {currentValues.min.toFixed(2)} {selectedType?.unit}
                </div>
              </Col>
              <Col span={8}>
                <div style={{ fontSize: '10px', color: '#a6a6a6' }}>Avg</div>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#e0e0e0' }}>
                  {currentValues.avg.toFixed(2)} {selectedType?.unit}
                </div>
              </Col>
              <Col span={8}>
                <div style={{ fontSize: '10px', color: '#a6a6a6' }}>Max</div>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#e0e0e0' }}>
                  {currentValues.max.toFixed(2)} {selectedType?.unit}
                </div>
              </Col>
            </Row>
          </div>
        )}

        {/* Adjustment Mode */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Adjustment Mode:
          </div>
          <Row gutter={8}>
            <Col span={12}>
              <Button
                type={adjustmentMode === 'absolute' ? 'primary' : 'default'}
                size="small"
                onClick={() => setAdjustmentMode('absolute')}
                style={{ width: '100%' }}
              >
                Set To
              </Button>
            </Col>
            <Col span={12}>
              <Button
                type={adjustmentMode === 'relative' ? 'primary' : 'default'}
                size="small"
                onClick={() => setAdjustmentMode('relative')}
                style={{ width: '100%' }}
              >
                Adjust By
              </Button>
            </Col>
          </Row>
        </div>

        {/* Value Input */}
        {selectedType && (
          <div>
            <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
              {adjustmentMode === 'absolute' ? 'New Value:' : 'Adjustment:'}
            </div>
            
            {viewMode === 'detailed' ? (
              <div>
                <Slider
                  min={selectedType.min}
                  max={selectedType.max}
                  step={selectedType.step}
                  value={adjustmentValue}
                  onChange={setAdjustmentValue}
                  tooltip={{
                    formatter: (value) => `${value} ${selectedType.unit}`
                  }}
                />
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                  <InputNumber
                    min={selectedType.min}
                    max={selectedType.max}
                    step={selectedType.step}
                    value={adjustmentValue}
                    onChange={setAdjustmentValue}
                    addonAfter={selectedType.unit}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            ) : (
              <InputNumber
                min={selectedType.min}
                max={selectedType.max}
                step={selectedType.step}
                value={adjustmentValue}
                onChange={setAdjustmentValue}
                addonAfter={selectedType.unit}
                style={{ width: '100%' }}
              />
            )}
          </div>
        )}

        {/* Application Options */}
        <div>
          <div style={{ marginBottom: 8, fontSize: '12px', fontWeight: 'bold' }}>
            Application:
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: '#e0e0e0' }}>Apply Immediately:</span>
            <Switch
              checked={applyImmediately}
              onChange={setApplyImmediately}
              size="small"
            />
          </div>
          <div style={{ fontSize: '10px', color: '#a6a6a6', marginTop: 4 }}>
            {applyImmediately 
              ? 'Changes will affect current and future trades'
              : 'Changes will only affect new trades'
            }
          </div>
        </div>

        {/* Preview */}
        {selectedType && affectedCount > 0 && (
          <div style={{ 
            padding: 12, 
            background: '#1f2a1f', 
            border: '1px solid #52c41a',
            borderRadius: 4 
          }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: 4, color: '#e0e0e0' }}>
              Adjustment Preview:
            </div>
            <div style={{ fontSize: '11px', color: '#a6a6a6' }}>
              <div>Parameter: <strong style={{ color: '#e0e0e0' }}>{selectedType.label}</strong></div>
              <div>Target: <strong style={{ color: '#e0e0e0' }}>{targetOptions.find(opt => opt.value === targetScope)?.label}</strong></div>
              <div>Affected EAs: <strong style={{ color: '#52c41a' }}>{affectedCount}</strong></div>
              <div>
                {adjustmentMode === 'absolute' ? 'New Value' : 'Final Value'}: 
                <strong style={{ color: '#00d4ff' }}>
                  {' '}{adjustmentMode === 'relative' 
                    ? (currentValues.avg + adjustmentValue).toFixed(2)
                    : adjustmentValue.toFixed(2)
                  } {selectedType.unit}
                </strong>
              </div>
            </div>
          </div>
        )}

        {/* Execute Button */}
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={executeRiskAdjustment}
          disabled={!selectedType || affectedCount === 0}
          loading={loading}
          style={{ width: '100%' }}
        >
          Apply Risk Adjustment
        </Button>

        {/* Quick Presets */}
        {viewMode === 'detailed' && (
          <>
            <Divider style={{ margin: '12px 0' }}>Quick Presets</Divider>
            <Row gutter={[8, 8]}>
              <Col span={8}>
                <Button
                  size="small"
                  onClick={() => {
                    setAdjustmentType('risk_percent');
                    setAdjustmentValue(1.0);
                    setAdjustmentMode('absolute');
                  }}
                  style={{ width: '100%' }}
                >
                  Low Risk
                </Button>
              </Col>
              <Col span={8}>
                <Button
                  size="small"
                  onClick={() => {
                    setAdjustmentType('risk_percent');
                    setAdjustmentValue(2.0);
                    setAdjustmentMode('absolute');
                  }}
                  style={{ width: '100%' }}
                >
                  Medium Risk
                </Button>
              </Col>
              <Col span={8}>
                <Button
                  size="small"
                  onClick={() => {
                    setAdjustmentType('risk_percent');
                    setAdjustmentValue(3.0);
                    setAdjustmentMode('absolute');
                  }}
                  style={{ width: '100%' }}
                >
                  High Risk
                </Button>
              </Col>
            </Row>
          </>
        )}
      </Space>
    </Card>
  );
};

export default RiskAdjustmentInterface;