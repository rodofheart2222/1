import React from 'react';
import { Alert, List, Badge, Tag, Row, Col, Tooltip } from 'antd';
import {
  RobotOutlined,
  DollarOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import './ExpertsPanel.css';

const ExpertsPanel = ({ eaData = [] }) => {
  // Now uses eaData prop from parent Dashboard component instead of independent API calls

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const getEAStatusBadge = (ea) => {
    const isActive = ea.openPositions > 0 || ea.open_positions > 0;
    const isPaused = ea.isPaused || ea.is_paused;
    
    if (isPaused) {
      return <Badge status="warning" text="Paused" />;
    } else if (isActive) {
      return <Badge status="processing" text="Trading" />;
    } else {
      return <Badge status="default" text="Monitoring" />;
    }
  };

  const getPerformanceColor = (profit) => {
    if (profit > 0) return '#52c41a';
    if (profit < 0) return '#ff4d4f';
    return '#d9d9d9';
  };

  const getTimeSinceUpdate = (lastUpdate) => {
    if (!lastUpdate) return 'Unknown';
    
    try {
      const now = new Date();
      const updateTime = new Date(lastUpdate);
      
      if (isNaN(updateTime.getTime())) {
        return 'Invalid';
      }
      
      const diffMs = now - updateTime;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch (error) {
      return 'Unknown';
    }
  };

  // Loading and error states are now handled by parent Dashboard component

  if (!eaData || eaData.length === 0) {
    return (
      <Alert
        message="No Expert Advisors"
        description="No EAs are currently running or connected to the system"
        type="info"
        showIcon
        style={{ margin: '16px 0' }}
      />
    );
  }

  // Calculate summary stats
  const totalEAs = eaData.length;
  const activeEAs = eaData.filter(ea => (ea.openPositions || ea.open_positions || 0) > 0).length;
  const totalProfit = eaData.reduce((sum, ea) => sum + (ea.currentProfit || ea.current_profit || 0), 0);
  const totalPositions = eaData.reduce((sum, ea) => sum + (ea.openPositions || ea.open_positions || 0), 0);

  return (
    <div className="experts-panel">
      <div className="experts-panel-header">
        <div className="panel-title">
          <RobotOutlined style={{ marginRight: '8px', color: '#1565C0' }} />
          Expert Advisors
        </div>
        <div className="ea-count">
          {activeEAs}/{totalEAs} Active
        </div>
      </div>

      {/* Summary Stats */}
      <div className="ea-summary-stats">
        <Row gutter={[8, 8]}>
          <Col span={12}>
            <div className="stat-card">
              <div className="stat-icon">
                <DollarOutlined style={{ color: getPerformanceColor(totalProfit) }} />
              </div>
              <div className="stat-content">
                <div className="stat-label">Total P&L</div>
                <div className="stat-value" style={{ color: getPerformanceColor(totalProfit) }}>
                  {formatCurrency(totalProfit)}
                </div>
              </div>
            </div>
          </Col>
          <Col span={12}>
            <div className="stat-card">
              <div className="stat-icon">
                <BarChartOutlined style={{ color: '#1565C0' }} />
              </div>
              <div className="stat-content">
                <div className="stat-label">Positions</div>
                <div className="stat-value">{totalPositions}</div>
              </div>
            </div>
          </Col>
        </Row>
      </div>

      {/* EA List */}
      <div className="ea-list">
        <List
          size="small"
          dataSource={eaData}
          renderItem={(ea) => {
            const profit = ea.currentProfit || ea.current_profit || 0;
            const positions = ea.openPositions || ea.open_positions || 0;
            const magicNumber = ea.magicNumber || ea.magic_number;
            const symbol = ea.symbol;
            const strategyTag = ea.strategyTag || ea.strategy_tag;
            const lastUpdate = ea.lastUpdate || ea.last_update;
            
            return (
              <List.Item className="ea-list-item">
                <div className="ea-item-content">
                  <div className="ea-item-header">
                    <div className="ea-symbol-magic">
                      <span className="ea-symbol">{symbol}</span>
                      <Tag size="small" color="blue">#{magicNumber}</Tag>
                    </div>
                    <div className="ea-status">
                      {getEAStatusBadge(ea)}
                    </div>
                  </div>
                  
                  <div className="ea-item-details">
                    <div className="ea-strategy">
                      <Tag size="small" color="purple">{strategyTag}</Tag>
                    </div>
                    <div className="ea-metrics">
                      <Tooltip title="Current Profit/Loss">
                        <span style={{ 
                          color: getPerformanceColor(profit),
                          fontWeight: '600',
                          fontSize: '12px'
                        }}>
                          {formatCurrency(profit)}
                        </span>
                      </Tooltip>
                      {positions > 0 && (
                        <Tooltip title="Open Positions">
                          <span style={{ marginLeft: '8px', fontSize: '11px' }}>
                            {positions} pos
                          </span>
                        </Tooltip>
                      )}
                    </div>
                  </div>
                  
                  <div className="ea-item-footer">
                    <span className="ea-last-update">
                      {getTimeSinceUpdate(lastUpdate)}
                    </span>
                  </div>
                </div>
              </List.Item>
            );
          }}
        />
      </div>
    </div>
  );
};

export default ExpertsPanel;