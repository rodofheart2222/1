import React, { useState } from 'react';
import { Card, Row, Col, Table, Statistic, Progress, Tag, Tabs, Select, Space } from 'antd';
import { 
  ArrowUpOutlined, 
  ArrowDownOutlined, 
  DollarOutlined,
  TrophyOutlined,
  BarChartOutlined,
  PieChartOutlined
} from '@ant-design/icons';

// Removed deprecated TabPane destructuring
const { Option } = Select;

const PerformanceBreakdownPanel = ({ data, viewMode = 'summary', showCharts = false }) => {
  const [breakdownType, setBreakdownType] = useState('symbol');
  const [sortBy, setSortBy] = useState('totalPnL');
  const [sortOrder, setSortOrder] = useState('descend');

  const { bySymbol = [], byStrategy = [] } = data || {};

  // Get current data based on breakdown type with null safety
  const currentData = breakdownType === 'symbol' ? (bySymbol || []) : (byStrategy || []);

  // Sort data with null safety
  const sortedData = [...(currentData || [])].sort((a, b) => {
    const aVal = a?.[sortBy] || 0;
    const bVal = b?.[sortBy] || 0;
    return sortOrder === 'ascend' ? aVal - bVal : bVal - aVal;
  });

  // Table columns for detailed view
  const getColumns = () => {
    const baseColumns = [
      {
        title: breakdownType === 'symbol' ? 'Symbol' : 'Strategy',
        dataIndex: breakdownType === 'symbol' ? 'symbol' : 'strategy',
        key: 'name',
        render: (text) => (
          <Tag color={breakdownType === 'symbol' ? 'blue' : 'green'}>
            {text}
          </Tag>
        ),
      },
      {
        title: 'P&L',
        dataIndex: 'totalPnL',
        key: 'totalPnL',
        render: (value) => (
          <Statistic
            value={value}
            precision={2}
            valueStyle={{ 
              color: value >= 0 ? '#3f8600' : '#cf1322',
              fontSize: '14px'
            }}
            prefix={value >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            suffix="USD"
          />
        ),
        sorter: true,
      },
      {
        title: 'Active/Total EAs',
        key: 'eas',
        render: (_, record) => (
          <span>
            <Tag color={record.activeEAs === record.totalEAs ? 'green' : 'orange'}>
              {record.activeEAs}/{record.totalEAs}
            </Tag>
          </span>
        ),
      },
      {
        title: 'Win Rate',
        dataIndex: 'winRate',
        key: 'winRate',
        render: (value) => (
          <div style={{ width: 80 }}>
            <Progress
              percent={value}
              size="small"
              strokeColor={value >= 60 ? '#52c41a' : value >= 40 ? '#faad14' : '#ff4d4f'}
              format={(percent) => `${percent}%`}
            />
          </div>
        ),
      },
    ];

    if (viewMode === 'detailed') {
      baseColumns.push(
        {
          title: 'Profit Factor',
          dataIndex: 'avgProfitFactor',
          key: 'avgProfitFactor',
          render: (value) => (
            <Statistic
              value={value}
              precision={2}
              valueStyle={{ fontSize: '14px' }}
            />
          ),
        },
        {
          title: 'Drawdown',
          dataIndex: 'totalDrawdown',
          key: 'totalDrawdown',
          render: (value) => (
            <div style={{ width: 80 }}>
              <Progress
                percent={Math.min(value, 100)}
                size="small"
                strokeColor="#ff4d4f"
                format={(percent) => `${percent}%`}
              />
            </div>
          ),
        }
      );
    }

    return baseColumns;
  };

  // Summary cards for quick overview
  const renderSummaryCards = () => {
    if ((sortedData || []).length === 0) return null;

    const topPerformers = (sortedData || []).slice(0, 3);
    
    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {topPerformers.map((item, index) => {
          const name = item.symbol || item.strategy;
          const isProfit = item.totalPnL >= 0;
          
          return (
            <Col span={8} key={name}>
              <Card size="small" className={`performance-card ${isProfit ? 'profit' : 'loss'}`}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: 4 }}>
                    #{index + 1} {breakdownType === 'symbol' ? 'Symbol' : 'Strategy'}
                  </div>
                  <Tag color={breakdownType === 'symbol' ? 'blue' : 'green'} style={{ marginBottom: 8 }}>
                    {name}
                  </Tag>
                  <Statistic
                    value={item.totalPnL}
                    precision={2}
                    valueStyle={{ 
                      color: isProfit ? '#3f8600' : '#cf1322',
                      fontSize: '16px'
                    }}
                    prefix={<DollarOutlined />}
                    suffix="USD"
                  />
                  <div style={{ marginTop: 8, fontSize: '11px', color: '#666' }}>
                    {item.activeEAs}/{item.totalEAs} EAs Active
                  </div>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>
    );
  };

  // Chart placeholder (would integrate with actual charting library)
  const renderCharts = () => {
    if (!showCharts) return null;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card 
            title="P&L Distribution" 
            size="small"
            extra={<BarChartOutlined />}
          >
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
              Chart: P&L by {breakdownType === 'symbol' ? 'Symbol' : 'Strategy'}
              <br />
              <small>(Chart integration pending)</small>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card 
            title="EA Distribution" 
            size="small"
            extra={<PieChartOutlined />}
          >
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
              Chart: EA Count by {breakdownType === 'symbol' ? 'Symbol' : 'Strategy'}
              <br />
              <small>(Chart integration pending)</small>
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  return (
    <Card
      title="Performance Breakdown"
      className="performance-breakdown-panel"
      extra={
        <Space>
          <Select
            value={breakdownType}
            onChange={setBreakdownType}
            size="small"
            style={{ width: 100 }}
          >
            <Option value="symbol">Symbol</Option>
            <Option value="strategy">Strategy</Option>
          </Select>
          <Select
            value={sortBy}
            onChange={setSortBy}
            size="small"
            style={{ width: 120 }}
          >
            <Option value="totalPnL">P&L</Option>
            <Option value="totalEAs">EA Count</Option>
            <Option value="winRate">Win Rate</Option>
            <Option value="avgProfitFactor">Profit Factor</Option>
          </Select>
        </Space>
      }
    >
      {/* Charts Section */}
      {renderCharts()}

      {/* Summary Cards */}
      {viewMode === 'summary' && renderSummaryCards()}

      {/* Detailed Table */}
      {(viewMode === 'detailed' || showCharts) && (
        <Table
          dataSource={sortedData || []}
          columns={getColumns()}
          rowKey={breakdownType === 'symbol' ? 'symbol' : 'strategy'}
          size="small"
          pagination={false}
          onChange={(pagination, filters, sorter) => {
            if (sorter?.field) {
              setSortBy(sorter.field);
              setSortOrder(sorter.order);
            }
          }}
        />
      )}

      {/* Empty State */}
      {(sortedData || []).length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#666' }}>
          <TrophyOutlined style={{ fontSize: '48px', marginBottom: 16 }} />
          <div>No performance data available</div>
          <div style={{ fontSize: '12px', marginTop: 8 }}>
            Connect EAs to see performance breakdown
          </div>
        </div>
      )}
    </Card>
  );
};

export default PerformanceBreakdownPanel;