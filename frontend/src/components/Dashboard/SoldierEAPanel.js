import React, { useState } from 'react';
import { 
  Card, 
  Tag, 
  Statistic, 
  Row, 
  Col, 
  Progress, 
  Tooltip, 
  Badge, 
  Collapse,
  List,
  Divider,
  Space,
  Typography
} from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  DollarOutlined,
  TrophyOutlined,
  WarningOutlined,
  LineChartOutlined,
  HistoryOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  CaretRightOutlined
} from '@ant-design/icons';
import PriceChart from '../Charts/PriceChart';

const { Panel } = Collapse;
const { Text } = Typography;

const SoldierEAPanel = ({ eaData }) => {
  const [expandedSections, setExpandedSections] = useState(['live-info', 'chart']);
  
  // Handle case where eaData is undefined or null
  if (!eaData) {
    return (
      <Card
        size="small"
        title="No EA Data"
        className="soldier-ea-panel"
      >
        <div style={{ textAlign: 'center', color: '#999', fontSize: '12px' }}>
          EA data is not available
        </div>
      </Card>
    );
  }
  
  const {
    magic_number,
    symbol,
    strategy_tag,
    current_profit = 0,
    open_positions = 0,
    sl_value = 0,
    tp_value = 0,
    trailing_active = false,
    sl_method = 'ATR',
    tp_method = 'Structure',
    module_status = {},
    performance_metrics = {},
    last_trades = [],
    coc_override = false,
    coc_command = null,
    last_update,
    trade_status = 'No Position',
    order_type = null,
    volume = 0,
    entry_price = 0,
    themeData = {}  // Portfolio analytics theme data
  } = eaData;

  const {
    total_profit = 0,
    profit_factor = 0,
    expected_payoff = 0,
    drawdown = 0,
    z_score = 0,
    win_rate = 0,
    trade_count = 0
  } = performance_metrics;

  // Apply portfolio analytics theme colors
  const profitColor = themeData.profitIndicator?.color || (current_profit >= 0 ? '#00ffaa' : '#ff4d99');
  const statusColor = themeData.statusIndicator?.color || '#00d4ff';
  const isActive = open_positions > 0;
  const isHealthy = profit_factor > 1.2 && drawdown < 20;
  
  // Portfolio theme styling
  const portfolioCardStyle = themeData.glassEffect ? {
    background: themeData.glassEffect.background,
    backdropFilter: themeData.glassEffect.backdropFilter,
    border: themeData.glassEffect.border,
    borderRadius: themeData.glassEffect.borderRadius,
    boxShadow: themeData.glassEffect.boxShadow,
    ...themeData.statusIndicator?.pulseAnimation && {
      animation: 'pulse-glow 2s ease-in-out infinite'
    }
  } : {};

  // Module status indicators with portfolio theme
  const getModuleStatusColor = (status) => {
    const themeColors = themeData.moduleStatusTheme || {};
    switch (status?.toLowerCase()) {
      case 'active': return themeColors.activeColor || '#00ffaa';
      case 'signal': return themeColors.warningColor || '#faad14';
      case 'inactive': return themeColors.inactiveColor || '#666666';
      case 'error': return themeColors.errorColor || '#ff4d99';
      case 'trend': return statusColor || '#00d4ff';
      case 'compression': return '#9c27b0';
      case 'expansion': return '#00bcd4';
      default: return themeColors.inactiveColor || '#666666';
    }
  };

  const getModuleIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': return <CheckCircleOutlined />;
      case 'signal': return <WarningOutlined />;
      case 'inactive': return <CloseCircleOutlined />;
      default: return <MinusCircleOutlined />;
    }
  };

  // Time since last update
  const getTimeSinceUpdate = () => {
    if (!last_update) return 'Unknown';
    
    try {
      const now = new Date();
      const lastUpdate = new Date(last_update);
      
      // Check if the date is valid
      if (isNaN(lastUpdate.getTime())) {
        return 'Invalid date';
      }
      
      const diffMs = now - lastUpdate;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch (error) {
      console.warn('Error parsing last_update timestamp:', last_update, error);
      return 'Unknown';
    }
  };

  // Format trade string for display
  const formatTradeString = (tradeStr) => {
    if (!tradeStr) return 'No trade data';
    // Expected format: "[LIMIT] EURUSD Buy 1.0 @ 1.0850"
    return tradeStr;
  };

  // Get SL/TP activation method display
  const getActivationMethodColor = (method) => {
    switch (method?.toLowerCase()) {
      case 'atr': return 'blue';
      case 'structure': return 'green';
      case 'buffer': return 'orange';
      default: return 'default';
    }
  };

  return (
    <Badge.Ribbon 
      text={coc_override ? 'COC Override' : (isActive ? 'Active' : 'Inactive')} 
      color={coc_override ? 'red' : (isActive ? 'green' : 'default')}
    >
      <Card
        size="small"
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: statusColor, textShadow: themeData.statusIndicator?.glowEffect }}>{symbol}</span>
            <div>
              {isActive ? <PlayCircleOutlined style={{ color: '#00ffaa', filter: 'drop-shadow(0 0 4px #00ffaa50)' }} /> : 
                         <PauseCircleOutlined style={{ color: '#666666' }} />}
              {!isHealthy && <WarningOutlined style={{ color: '#faad14', marginLeft: 4, filter: 'drop-shadow(0 0 4px #faad1450)' }} />}
            </div>
          </div>
        }
        extra={
          <Tag 
            style={{ 
              background: themeData.performanceTheme?.backgroundGradient || 'linear-gradient(135deg, #00d4ff 0%, rgba(255, 255, 255, 0.2) 100%)',
              border: `1px solid ${statusColor}`,
              color: '#ffffff',
              boxShadow: themeData.statusIndicator?.glowEffect
            }}
          >
            #{magic_number}
          </Tag>
        }
        className="soldier-ea-panel glass-ea-card"
        style={portfolioCardStyle}
      >
        {/* Strategy Tag and Update Time */}
        <div style={{ marginBottom: 12 }}>
          <Space>
            <Tag color="purple">{strategy_tag}</Tag>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              Updated: {getTimeSinceUpdate()}
            </Text>
          </Space>
        </div>

        {/* Collapsible Sections */}
        <Collapse 
          size="small" 
          ghost
          activeKey={expandedSections}
          onChange={setExpandedSections}
          expandIcon={({ isActive }) => <CaretRightOutlined rotate={isActive ? 90 : 0} />}
        >
          {/* Price Chart Panel */}
          <Panel 
            header={
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <LineChartOutlined />
                <span>Price Chart</span>
              </div>
            } 
            key="chart"
          >
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>
              <PriceChart 
                symbol={symbol} 
                width={280} 
                height={160} 
                showControls={true}
              />
            </div>
          </Panel>

          {/* Live Trade Info Panel */}
          <Panel header="Live Trade Info" key="live-info">
            <Row gutter={8} style={{ marginBottom: 8 }}>
              <Col span={12}>
                <Statistic
                  title="Current P&L"
                  value={current_profit}
                  precision={2}
                  valueStyle={{ 
                    color: profitColor, 
                    fontSize: '13px',
                    textShadow: themeData.profitIndicator?.glowEffect,
                    background: themeData.profitIndicator?.gradient,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}
                  prefix={<DollarOutlined style={{ color: profitColor, filter: `drop-shadow(0 0 4px ${profitColor}50)` }} />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Positions"
                  value={open_positions}
                  valueStyle={{ fontSize: '13px' }}
                />
              </Col>
            </Row>
            
            {/* Trade Status Details */}
            <div style={{ fontSize: '11px', marginBottom: 8 }}>
              <div><strong>Status:</strong> {trade_status}</div>
              {order_type && <div><strong>Type:</strong> {order_type}</div>}
              {volume > 0 && <div><strong>Volume:</strong> {volume}</div>}
              {entry_price > 0 && <div><strong>Entry:</strong> {entry_price.toFixed(5)}</div>}
            </div>
          </Panel>

          {/* Module Status Grid Panel */}
          <Panel header="Module Status" key="modules">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))', gap: 8 }}>
              {Object.entries(module_status).map(([module, status]) => (
                <Tooltip key={module} title={`${module}: ${status}`}>
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '4px', 
                    border: `1px solid ${getModuleStatusColor(status)}`,
                    borderRadius: '4px',
                    backgroundColor: themeData.moduleStatusTheme?.glassBackground || `${getModuleStatusColor(status)}15`,
                    backdropFilter: 'blur(5px)',
                    boxShadow: `0 0 8px ${getModuleStatusColor(status)}30`
                  }}>
                    <div style={{ fontSize: '10px', fontWeight: 'bold' }}>{module.toUpperCase()}</div>
                    <div style={{ fontSize: '9px', color: getModuleStatusColor(status) }}>
                      {getModuleIcon(status)} {status}
                    </div>
                  </div>
                </Tooltip>
              ))}
            </div>
          </Panel>

          {/* SL/TP and Trailing Status Panel */}
          <Panel header="SL/TP & Trailing" key="sl-tp">
            <Row gutter={8} style={{ marginBottom: 8 }}>
              <Col span={12}>
                <div style={{ fontSize: '11px' }}>
                  <div><strong>Stop Loss:</strong></div>
                  <div>{sl_value > 0 ? sl_value.toFixed(5) : 'Not Set'}</div>
                  <Tag size="small" color={getActivationMethodColor(sl_method)}>
                    {sl_method || 'Manual'}
                  </Tag>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ fontSize: '11px' }}>
                  <div><strong>Take Profit:</strong></div>
                  <div>{tp_value > 0 ? tp_value.toFixed(5) : 'Not Set'}</div>
                  <Tag size="small" color={getActivationMethodColor(tp_method)}>
                    {tp_method || 'Manual'}
                  </Tag>
                </div>
              </Col>
            </Row>
            
            <div style={{ textAlign: 'center' }}>
              <Tag 
                color={trailing_active ? 'green' : 'default'} 
                icon={trailing_active ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              >
                Trailing {trailing_active ? 'Active' : 'Inactive'}
              </Tag>
            </div>
          </Panel>

          {/* Performance Metrics Panel */}
          <Panel header="Performance Metrics" key="performance">
            <Row gutter={8} style={{ marginBottom: 8 }}>
              <Col span={8}>
                <Tooltip title="Profit Factor">
                  <Statistic
                    title="PF"
                    value={profit_factor}
                    precision={2}
                    valueStyle={{ 
                      color: profit_factor > 1 ? '#52c41a' : '#ff4d4f',
                      fontSize: '12px'
                    }}
                  />
                </Tooltip>
              </Col>
              <Col span={8}>
                <Tooltip title="Drawdown Percentage">
                  <Statistic
                    title="DD%"
                    value={drawdown}
                    precision={1}
                    suffix="%"
                    valueStyle={{ 
                      color: drawdown > 20 ? '#ff4d4f' : '#52c41a',
                      fontSize: '12px'
                    }}
                  />
                </Tooltip>
              </Col>
              <Col span={8}>
                <Tooltip title="Z-Score">
                  <Statistic
                    title="Z-Score"
                    value={z_score}
                    precision={2}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Tooltip>
              </Col>
            </Row>
            
            <Row gutter={8}>
              <Col span={8}>
                <Tooltip title="Total Profit">
                  <Statistic
                    title="Total"
                    value={total_profit}
                    precision={0}
                    prefix="$"
                    valueStyle={{ 
                      color: total_profit >= 0 ? '#52c41a' : '#ff4d4f',
                      fontSize: '12px'
                    }}
                  />
                </Tooltip>
              </Col>
              <Col span={8}>
                <Tooltip title="Win Rate">
                  <Statistic
                    title="Win%"
                    value={win_rate}
                    precision={1}
                    suffix="%"
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Tooltip>
              </Col>
              <Col span={8}>
                <Tooltip title="Trade Count">
                  <Statistic
                    title="Trades"
                    value={trade_count}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Tooltip>
              </Col>
            </Row>
          </Panel>

          {/* Trade Journal Panel */}
          <Panel header="Trade Journal" key="trades">
            {(last_trades || []).length > 0 ? (
              <List
                size="small"
                dataSource={(last_trades || []).slice(0, 10)}
                renderItem={(trade, index) => (
                  <List.Item style={{ padding: '4px 0', fontSize: '10px' }}>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text style={{ fontSize: '10px' }}>{formatTradeString(trade)}</Text>
                        <Text type="secondary" style={{ fontSize: '9px' }}>#{index + 1}</Text>
                      </div>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#999', fontSize: '11px' }}>
                No recent trades
              </div>
            )}
          </Panel>

          {/* Commander Override Status Panel */}
          {coc_override && (
            <Panel header="Commander Override" key="override">
              <div style={{ 
                padding: '8px', 
                backgroundColor: '#fff2e8', 
                border: '1px solid #ffbb96',
                borderRadius: '4px'
              }}>
                <div style={{ fontSize: '11px', marginBottom: 4 }}>
                  <WarningOutlined style={{ color: '#fa8c16', marginRight: 4 }} />
                  <strong>Override Active</strong>
                </div>
                {coc_command && (
                  <div style={{ fontSize: '10px', color: '#666' }}>
                    Command: {coc_command}
                  </div>
                )}
                <div style={{ fontSize: '10px', color: '#666', marginTop: 4 }}>
                  Manual control enabled - EA decisions overridden
                </div>
              </div>
            </Panel>
          )}
        </Collapse>
      </Card>
    </Badge.Ribbon>
  );
};

export default SoldierEAPanel;