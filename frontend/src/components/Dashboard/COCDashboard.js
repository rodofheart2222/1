import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Tabs, Select, Button, Space, Divider } from 'antd';

const { TabPane } = Tabs;
import {
  DashboardOutlined,
  BarChartOutlined,
  FilterOutlined,
  ControlOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  GroupOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useDashboard } from '../../context/DashboardContext';
import GlobalStatsPanel from './GlobalStatsPanel';
import PerformanceBreakdownPanel from './PerformanceBreakdownPanel';
import FilterPanel from './FilterPanel';
import GlobalActionControls from './GlobalActionControls';
import RiskAdjustmentInterface from './RiskAdjustmentInterface';
import ActionQueuePanel from './ActionQueuePanel';
import EAGroupingPanel from './EAGroupingPanel';
import BacktestComparisonPanel from './BacktestComparisonPanel';
import './COCDashboard.css';

const { Option } = Select;

const COCDashboard = () => {
  const { state, actions } = useDashboard();
  const { eaData, globalStats, filters, commandQueue } = state;

  const [activeTab, setActiveTab] = useState('overview');
  const [viewMode, setViewMode] = useState('summary'); // summary, detailed

  // Calculate filtered EA data based on current filters
  const filteredEAData = useMemo(() => {
    return (eaData || []).filter(ea => {
      if (!ea) return false;
      if (filters?.symbol !== 'all' && ea.symbol !== filters.symbol) return false;
      if (filters?.strategy !== 'all' && ea.strategy_tag !== filters.strategy) return false;
      if (filters?.status !== 'all') {
        const isActive = (ea.open_positions || 0) > 0 || ea.status === 'active';
        if (filters.status === 'active' && !isActive) return false;
        if (filters.status === 'inactive' && isActive) return false;
      }
      if (filters?.search && ea.symbol && ea.strategy_tag &&
        !ea.symbol.toLowerCase().includes(filters.search.toLowerCase()) &&
        !ea.strategy_tag.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [eaData, filters]);

  // Calculate performance breakdown data
  const performanceBreakdown = useMemo(() => {
    const bySymbol = {};
    const byStrategy = {};

    (filteredEAData || []).forEach(ea => {
      if (!ea?.symbol || !ea?.strategy_tag) return;

      // By Symbol
      if (!bySymbol[ea.symbol]) {
        bySymbol[ea.symbol] = {
          symbol: ea.symbol,
          totalPnL: 0,
          activeEAs: 0,
          totalEAs: 0,
          avgProfitFactor: 0,
          totalDrawdown: 0,
          winRate: 0
        };
      }

      bySymbol[ea.symbol].totalPnL += ea.current_profit || 0;
      bySymbol[ea.symbol].totalEAs += 1;
      if ((ea.open_positions || 0) > 0) bySymbol[ea.symbol].activeEAs += 1;

      // By Strategy
      if (!byStrategy[ea.strategy_tag]) {
        byStrategy[ea.strategy_tag] = {
          strategy: ea.strategy_tag,
          totalPnL: 0,
          activeEAs: 0,
          totalEAs: 0,
          avgProfitFactor: 0,
          totalDrawdown: 0,
          winRate: 0
        };
      }

      byStrategy[ea.strategy_tag].totalPnL += ea.current_profit || 0;
      byStrategy[ea.strategy_tag].totalEAs += 1;
      if ((ea.open_positions || 0) > 0) byStrategy[ea.strategy_tag].activeEAs += 1;
    });

    return { bySymbol: Object.values(bySymbol), byStrategy: Object.values(byStrategy) };
  }, [filteredEAData]);

  const handleTabChange = (key) => {
    setActiveTab(key);
  };

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
  };

  return (
    <div className="coc-dashboard">
      {/* Header Controls */}
      <Card size="small" className="coc-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <DashboardOutlined style={{ fontSize: '18px', color: '#1890ff' }} />
              <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                Commander-in-Chief Dashboard
              </span>
              <Divider type="vertical" />
              <span style={{ color: '#666' }}>
                {(filteredEAData || []).length} of {(eaData || []).length} EAs
              </span>
            </Space>
          </Col>
          <Col>
            <Space>
              <Select
                value={viewMode}
                onChange={handleViewModeChange}
                size="small"
                style={{ width: 120 }}
              >
                <Option value="summary">Summary</Option>
                <Option value="detailed">Detailed</Option>
              </Select>
              <Button
                size="small"
                icon={<FilterOutlined />}
                onClick={() => setActiveTab('filters')}
              >
                Filters
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Dashboard Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        className="coc-tabs"
        tabBarStyle={{ marginBottom: 16 }}
      >
        {/* Overview Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
       
              Overview
            </span>
          }
          key="overview"
        >
          <Row gutter={[16, 16]}>
            {/* Global Statistics */}
            <Col span={24}>
              <GlobalStatsPanel
                data={globalStats || {}}
                filteredData={filteredEAData || []}
                viewMode={viewMode}
              />
            </Col>

            {/* Performance Breakdown */}
            <Col span={24}>
              <PerformanceBreakdownPanel
                data={performanceBreakdown || {}}
                viewMode={viewMode}
              />
            </Col>
          </Row>
        </TabPane>

        {/* Performance Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
        
              Performance
            </span>
          }
          key="performance"
        >
          <PerformanceBreakdownPanel
            data={performanceBreakdown || {}}
            viewMode="detailed"
            showCharts={true}
          />
        </TabPane>

        {/* Filters Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
            
              Filters
            </span>
          }
          key="filters"
        >
          <FilterPanel
            eaData={eaData || []}
            filters={filters || {}}
            onFiltersChange={actions.setFilters}
          />
        </TabPane>

        {/* Controls Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
            
              Controls
            </span>
          }
          key="controls"
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <GlobalActionControls
                eaData={filteredEAData || []}
                onCommandExecute={actions.addCommand}
              />
            </Col>
            <Col span={12}>
              <RiskAdjustmentInterface
                eaData={filteredEAData || []}
                onRiskAdjust={actions.addCommand}
              />
            </Col>
          </Row>
        </TabPane>

        {/* Risk Management Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
            
              Risk Management
            </span>
          }
          key="risk"
        >
          <RiskAdjustmentInterface
            eaData={filteredEAData || []}
            onRiskAdjust={actions.addCommand}
            viewMode="detailed"
          />
        </TabPane>

        {/* Action Queue Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
             
              Action Queue ({(commandQueue || []).length})
            </span>
          }
          key="queue"
        >
          <ActionQueuePanel
            commandQueue={commandQueue || []}
            onCommandUpdate={actions.updateCommand}
            onQueueClear={actions.clearCommandQueue}
          />
        </TabPane>

        {/* EA Grouping Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
          
              EA Grouping
            </span>
          }
          key="grouping"
        >
          <EAGroupingPanel />
        </TabPane>

        {/* Backtest Comparison Tab */}
        <TabPane
          tab={
            <span style={{ padding: '20px 20px' }}>
            
              Backtest Comparison
            </span>
          }
          key="backtest"
        >
          <BacktestComparisonPanel />
        </TabPane>
      </Tabs>
    </div>
  );
};

export default COCDashboard;