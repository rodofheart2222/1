import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Select, Input, Button, Space, Tag, Divider, Slider } from 'antd';
import { 
  FilterOutlined, 
  ClearOutlined, 
  SearchOutlined,
  DollarOutlined,
  PercentageOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { Search } = Input;

const FilterPanel = ({ eaData = [], filters, onFiltersChange }) => {
  const [tempFilters, setTempFilters] = useState(filters);

  // Extract unique values for filter options
  const filterOptions = useMemo(() => {
    const symbols = [...new Set(eaData.map(ea => ea.symbol))].sort();
    const strategies = [...new Set(eaData.map(ea => ea.strategy_tag))].sort();
    const riskLevels = [...new Set(eaData.map(ea => ea.risk_config || 'default'))].sort();
    
    return { symbols, strategies, riskLevels };
  }, [eaData]);

  // Calculate filter statistics
  const filterStats = useMemo(() => {
    const total = eaData.length;
    const active = eaData.filter(ea => ea.open_positions > 0).length;
    const profitable = eaData.filter(ea => (ea.current_profit || 0) > 0).length;
    const losing = eaData.filter(ea => (ea.current_profit || 0) < 0).length;
    
    return { total, active, profitable, losing };
  }, [eaData]);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...tempFilters, [key]: value };
    setTempFilters(newFilters);
  };

  const applyFilters = () => {
    onFiltersChange(tempFilters);
  };

  const resetFilters = () => {
    const defaultFilters = {
      symbol: 'all',
      strategy: 'all',
      status: 'all',
      riskLevel: 'all',
      search: '',
      profitRange: [-1000, 1000],
      drawdownMax: 100
    };
    setTempFilters(defaultFilters);
    onFiltersChange(defaultFilters);
  };

  const getFilteredCount = () => {
    return eaData.filter(ea => {
      if (tempFilters.symbol !== 'all' && ea.symbol !== tempFilters.symbol) return false;
      if (tempFilters.strategy !== 'all' && ea.strategy_tag !== tempFilters.strategy) return false;
      if (tempFilters.riskLevel !== 'all' && (ea.risk_config || 'default') !== tempFilters.riskLevel) return false;
      if (tempFilters.status !== 'all') {
        const isActive = ea.open_positions > 0;
        if (tempFilters.status === 'active' && !isActive) return false;
        if (tempFilters.status === 'inactive' && isActive) return false;
        if (tempFilters.status === 'profitable' && (ea.current_profit || 0) <= 0) return false;
        if (tempFilters.status === 'losing' && (ea.current_profit || 0) >= 0) return false;
      }
      if (tempFilters.search && 
          !ea.symbol.toLowerCase().includes(tempFilters.search.toLowerCase()) &&
          !ea.strategy_tag.toLowerCase().includes(tempFilters.search.toLowerCase())) {
        return false;
      }
      if (tempFilters.profitRange) {
        const profit = ea.current_profit || 0;
        if (profit < tempFilters.profitRange[0] || profit > tempFilters.profitRange[1]) return false;
      }
      return true;
    }).length;
  };

  const filteredCount = getFilteredCount();
  const hasActiveFilters = Object.values(tempFilters).some(value => 
    value !== 'all' && value !== '' && value !== null && 
    (Array.isArray(value) ? value.join(',') !== '-1000,1000' : true)
  );

  return (
    <Card
      title={
        <Space>
          Filter & Search EAs
          <Tag color={hasActiveFilters ? 'blue' : 'default'}>
            {filteredCount} of {eaData.length} EAs
          </Tag>
        </Space>
      }
      className="filter-panel"
      extra={
        <Space>
          <Button 
            size="small" 
            onClick={resetFilters}
            icon={<ClearOutlined />}
            disabled={!hasActiveFilters}
          >
            Clear All
          </Button>
          <Button 
            type="primary" 
            size="small" 
            onClick={applyFilters}
            disabled={JSON.stringify(tempFilters) === JSON.stringify(filters)}
          >
            Apply Filters
          </Button>
        </Space>
      }
    >
      <Row gutter={[16, 16]}>
        {/* Quick Stats */}
        <Col span={24}>
          <Card size="small" title="Quick Stats" className="filter-stats">
            <Row gutter={16}>
              <Col span={6}>
                <div className="stat-item">
                  <div className="stat-value">{filterStats.total}</div>
                  <div className="stat-label">Total EAs</div>
                </div>
              </Col>
              <Col span={6}>
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#52c41a' }}>{filterStats.active}</div>
                  <div className="stat-label">Active</div>
                </div>
              </Col>
              <Col span={6}>
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#1890ff' }}>{filterStats.profitable}</div>
                  <div className="stat-label">Profitable</div>
                </div>
              </Col>
              <Col span={6}>
                <div className="stat-item">
                  <div className="stat-value" style={{ color: '#ff4d4f' }}>{filterStats.losing}</div>
                  <div className="stat-label">Losing</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* Search */}
        <Col span={24}>
          <Search
            placeholder="Search by symbol or strategy name..."
            value={tempFilters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            onSearch={applyFilters}
            enterButton={<SearchOutlined />}
            allowClear
          />
        </Col>

        {/* Basic Filters */}
        <Col span={8}>
          <div className="filter-group">
            <div className="filter-label">Symbol</div>
            <Select
              value={tempFilters.symbol}
              onChange={(value) => handleFilterChange('symbol', value)}
              style={{ width: '100%' }}
              placeholder="All Symbols"
            >
              <Option value="all">All Symbols</Option>
              {filterOptions.symbols.map(symbol => (
                <Option key={symbol} value={symbol}>{symbol}</Option>
              ))}
            </Select>
          </div>
        </Col>

        <Col span={8}>
          <div className="filter-group">
            <div className="filter-label">Strategy</div>
            <Select
              value={tempFilters.strategy}
              onChange={(value) => handleFilterChange('strategy', value)}
              style={{ width: '100%' }}
              placeholder="All Strategies"
            >
              <Option value="all">All Strategies</Option>
              {filterOptions.strategies.map(strategy => (
                <Option key={strategy} value={strategy}>{strategy}</Option>
              ))}
            </Select>
          </div>
        </Col>

        <Col span={8}>
          <div className="filter-group">
            <div className="filter-label">Status</div>
            <Select
              value={tempFilters.status}
              onChange={(value) => handleFilterChange('status', value)}
              style={{ width: '100%' }}
              placeholder="All Status"
            >
              <Option value="all">All Status</Option>
              <Option value="active">Active (Trading)</Option>
              <Option value="inactive">Inactive</Option>
              <Option value="profitable">Profitable</Option>
              <Option value="losing">Losing</Option>
            </Select>
          </div>
        </Col>

        {/* Advanced Filters */}
        <Col span={24}>
          <Divider orientation="left" style={{ margin: '16px 0' }}>Advanced Filters</Divider>
        </Col>

        <Col span={12}>
          <div className="filter-group">
            <div className="filter-label">Risk Configuration</div>
            <Select
              value={tempFilters.riskLevel}
              onChange={(value) => handleFilterChange('riskLevel', value)}
              style={{ width: '100%' }}
              placeholder="All Risk Levels"
            >
              <Option value="all">All Risk Levels</Option>
              {filterOptions.riskLevels.map(level => (
                <Option key={level} value={level}>{level}</Option>
              ))}
            </Select>
          </div>
        </Col>

        <Col span={12}>
          <div className="filter-group">
            <div className="filter-label">
              <Space>
                <DollarOutlined />
                Profit Range (USD)
              </Space>
            </div>
            <Slider
              range
              min={-1000}
              max={1000}
              step={50}
              value={tempFilters.profitRange || [-1000, 1000]}
              onChange={(value) => handleFilterChange('profitRange', value)}
              tooltip={{
                formatter: (value) => `$${value}`
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666' }}>
              <span>${tempFilters.profitRange?.[0] || -1000}</span>
              <span>${tempFilters.profitRange?.[1] || 1000}</span>
            </div>
          </div>
        </Col>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <Col span={24}>
            <Divider orientation="left" style={{ margin: '16px 0' }}>Active Filters</Divider>
            <Space wrap>
              {tempFilters.symbol !== 'all' && (
                <Tag 
                  closable 
                  onClose={() => handleFilterChange('symbol', 'all')}
                  color="blue"
                >
                  Symbol: {tempFilters.symbol}
                </Tag>
              )}
              {tempFilters.strategy !== 'all' && (
                <Tag 
                  closable 
                  onClose={() => handleFilterChange('strategy', 'all')}
                  color="green"
                >
                  Strategy: {tempFilters.strategy}
                </Tag>
              )}
              {tempFilters.status !== 'all' && (
                <Tag 
                  closable 
                  onClose={() => handleFilterChange('status', 'all')}
                  color="orange"
                >
                  Status: {tempFilters.status}
                </Tag>
              )}
              {tempFilters.riskLevel !== 'all' && (
                <Tag 
                  closable 
                  onClose={() => handleFilterChange('riskLevel', 'all')}
                  color="purple"
                >
                  Risk: {tempFilters.riskLevel}
                </Tag>
              )}
              {tempFilters.search && (
                <Tag 
                  closable 
                  onClose={() => handleFilterChange('search', '')}
                  color="cyan"
                >
                  Search: "{tempFilters.search}"
                </Tag>
              )}
            </Space>
          </Col>
        )}
      </Row>
    </Card>
  );
};

export default FilterPanel;