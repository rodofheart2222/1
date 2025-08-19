import React, { useState } from 'react';
import { Card, Row, Col, Input, Select, Tag, Empty, Switch, message, Modal } from 'antd';
import { SearchOutlined, LineChartOutlined } from '@ant-design/icons';
import SoldierEAPanel from './SoldierEAPanel';
import EACardWithChart from './EACardWithChart';
import ModernSkeleton from '../Common/ModernSkeleton';
import apiService from '../../services/api';

const { Search } = Input;
const { Option } = Select;

const EAGridView = ({ eaData = [] }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSymbol, setFilterSymbol] = useState('all');
  const [filterStrategy, setFilterStrategy] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showCharts, setShowCharts] = useState(true);

  // Get unique values for filters with null safety
  const symbols = [...new Set(eaData?.map(ea => ea?.symbol).filter(Boolean) || [])];
  const strategies = [...new Set(eaData?.map(ea => ea?.strategy_tag).filter(Boolean) || [])];

  // Filter EAs based on search and filters with null safety
  const filteredEAs = (eaData || []).filter(ea => {
    if (!ea) return false;
    
    const symbol = ea.symbol || '';
    const strategyTag = ea.strategy_tag || '';
    const magicNumber = ea.magic_number || 0;
    const openPositions = ea.open_positions || 0;
    const cocOverride = ea.coc_override || false;
    
    const matchesSearch = symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         strategyTag.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         magicNumber.toString().includes(searchTerm);
    
    const matchesSymbol = filterSymbol === 'all' || symbol === filterSymbol;
    const matchesStrategy = filterStrategy === 'all' || strategyTag === filterStrategy;
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'active' && openPositions > 0) ||
                         (filterStatus === 'inactive' && openPositions === 0) ||
                         (filterStatus === 'paused' && cocOverride);

    return matchesSearch && matchesSymbol && matchesStrategy && matchesStatus;
  });

  // Apply portfolio analytics theme to grid
  const portfolioTheme = {
    background: 'rgba(17, 17, 17, 0.88)',
    backdropFilter: 'blur(18px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '14px',
    boxShadow: '0 10px 35px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
  };

  // Command handlers for EA actions
  const handlePauseEA = async (ea) => {
    try {
      console.log('Pausing EA:', ea.magic_number);
      message.loading('Pausing EA...', 0.5);
      
      await apiService.sendEACommand(ea.magic_number, {
        command: 'pause',
        parameters: { reason: 'Dashboard pause request' },
        instance_uuid: ea.instance_uuid
      });
      
      message.success(`EA ${ea.magic_number} paused successfully`);
    } catch (error) {
      console.error('Failed to pause EA:', error);
      message.error(`Failed to pause EA: ${error.message}`);
    }
  };

  const handleResumeEA = async (ea) => {
    try {
      console.log('Resuming EA:', ea.magic_number);
      message.loading('Resuming EA...', 0.5);
      
      await apiService.sendEACommand(ea.magic_number, {
        command: 'resume',
        parameters: { reason: 'Dashboard resume request' },
        instance_uuid: ea.instance_uuid
      });
      
      message.success(`EA ${ea.magic_number} resumed successfully`);
    } catch (error) {
      console.error('Failed to resume EA:', error);
      message.error(`Failed to resume EA: ${error.message}`);
    }
  };

  const handleConfigureEA = (ea) => {
    console.log('Configure EA:', ea.magic_number);
    
    Modal.info({
      title: `Configure EA ${ea.magic_number}`,
      width: 700,
      content: (
        <div>
          <p><strong>EA Information:</strong></p>
          <ul>
            <li><strong>Magic Number:</strong> {ea.magic_number}</li>
            <li><strong>Symbol:</strong> {ea.symbol}</li>
            <li><strong>Strategy:</strong> {ea.strategy_tag}</li>
            <li><strong>Status:</strong> {ea.status}</li>
            <li><strong>Instance UUID:</strong> {ea.instance_uuid}</li>
          </ul>
          
          <p><strong>Current Settings:</strong></p>
          <ul>
            <li><strong>Is Paused:</strong> {ea.is_paused ? 'Yes' : 'No'}</li>
            <li><strong>Open Positions:</strong> {ea.open_positions || 0}</li>
            <li><strong>Current Profit:</strong> ${(ea.current_profit || 0).toFixed(2)}</li>
            <li><strong>Stop Loss:</strong> {ea.sl_value || 'Not set'}</li>
            <li><strong>Take Profit:</strong> {ea.tp_value || 'Not set'}</li>
          </ul>
          
          <p><strong>Available Actions:</strong></p>
          <ul>
            <li>Use pause/resume buttons for EA control</li>
            <li>Use Global Actions for advanced commands</li>
            <li>Use Global Actions for multiple EA operations</li>
          </ul>
          
          <p><em>Advanced EA configuration panel with risk settings, strategy parameters, and real-time adjustments coming soon...</em></p>
        </div>
      ),
      onOk() {}
    });
  };

  return (
    <div className="advanced-ea-grid-container glass-ea-grid" style={{ position: 'relative', ...portfolioTheme }}>
      {/* Enhanced Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        padding: '16px 0',
        borderBottom: '2px solid #1A1A1A',
        position: 'relative'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 12px',
              background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 212, 255, 0.1) 100%)',
              borderRadius: '8px',
              border: '1px solid rgba(0, 255, 136, 0.2)'
            }}>
              <div style={{
                width: '24px',
                height: '24px',
                background: 'linear-gradient(135deg, #00FF88 0%, #00D4FF 100%)',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ color: '#000', fontSize: '12px', fontWeight: '700' }}>
                  {filteredEAs.length}
                </span>
              </div>
              <div>
                <div style={{
                  color: '#E0E0E0',
                  fontSize: '14px',
                  fontWeight: '700',
                  lineHeight: '1'
                }}>
                  ACTIVE SYSTEMS
                </div>
                <div style={{
                  color: '#666',
                  fontSize: '10px',
                  lineHeight: '1'
                }}>
                  of {eaData.length} total
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Advanced Filter Controls */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          flexWrap: 'wrap'
        }}>
          {/* Chart Toggle */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            padding: '6px 10px',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '6px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            transition: 'all 0.3s ease'
          }}>
            <LineChartOutlined style={{ 
              color: showCharts ? '#00FF88' : '#666666', 
              fontSize: '12px',
              transition: 'color 0.3s ease'
            }} />
            <span style={{ color: '#CCCCCC', fontSize: '11px', fontWeight: '600' }}>Charts</span>
            <Switch
              size="small"
              checked={showCharts}
              onChange={setShowCharts}
              style={{
                backgroundColor: showCharts ? '#00FF88' : '#333333'
              }}
            />
          </div>
          
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <Search
              placeholder="Search systems..."
              allowClear
              style={{ 
                width: 200,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px'
              }}
              prefix={<SearchOutlined style={{ color: '#666' }} />}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          {/* Filter Dropdowns */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <Select
              value={filterSymbol}
              style={{ 
                width: 120,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px'
              }}
              onChange={setFilterSymbol}
              dropdownStyle={{
                backgroundColor: '#1A1A1A',
                border: '1px solid #333'
              }}
            >
              <Option value="all">All Symbols</Option>
              {symbols.map(symbol => (
                <Option key={symbol} value={symbol}>{symbol}</Option>
              ))}
            </Select>
            
            <Select
              value={filterStrategy}
              style={{ 
                width: 150,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px'
              }}
              onChange={setFilterStrategy}
              dropdownStyle={{
                backgroundColor: '#1A1A1A',
                border: '1px solid #333'
              }}
            >
              <Option value="all">All Strategies</Option>
              {strategies.map(strategy => (
                <Option key={strategy} value={strategy}>{strategy}</Option>
              ))}
            </Select>
            
            <Select
              value={filterStatus}
              style={{ 
                width: 120,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px'
              }}
              onChange={setFilterStatus}
              dropdownStyle={{
                backgroundColor: '#1A1A1A',
                border: '1px solid #333'
              }}
            >
              <Option value="all">All Status</Option>
              <Option value="active">Active</Option>
              <Option value="inactive">Inactive</Option>
              <Option value="paused">Paused</Option>
            </Select>
          </div>
        </div>
      </div>

      {/* Performance Summary Bar */}
      {filteredEAs.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '12px',
          marginBottom: '20px',
          padding: '16px',
          background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.3) 0%, rgba(26, 26, 26, 0.3) 100%)',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.05)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#00FF88', fontSize: '18px', fontWeight: '700' }}>
              {filteredEAs.filter(ea => (ea.current_profit || 0) > 0).length}
            </div>
            <div style={{ color: '#666', fontSize: '10px' }}>Profitable</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#00D4FF', fontSize: '18px', fontWeight: '700' }}>
              {filteredEAs.filter(ea => (ea.open_positions || 0) > 0).length}
            </div>
            <div style={{ color: '#666', fontSize: '10px' }}>Active</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#FFAA44', fontSize: '18px', fontWeight: '700' }}>
              {filteredEAs.reduce((sum, ea) => sum + (ea.open_positions || 0), 0)}
            </div>
            <div style={{ color: '#666', fontSize: '10px' }}>Positions</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              color: filteredEAs.reduce((sum, ea) => sum + (ea.current_profit || 0), 0) >= 0 ? '#00FF88' : '#FF4466',
              fontSize: '18px', 
              fontWeight: '700' 
            }}>
              ${filteredEAs.reduce((sum, ea) => sum + (ea.current_profit || 0), 0).toFixed(2)}
            </div>
            <div style={{ color: '#666', fontSize: '10px' }}>Total P&L</div>
          </div>
        </div>
      )}

      {/* Grid Content */}
      <div className="ea-grid-content">
        {eaData.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.2) 0%, rgba(26, 26, 26, 0.2) 100%)',
            borderRadius: '12px',
            border: '2px dashed rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              background: 'linear-gradient(135deg, #333 0%, #555 100%)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px'
            }}>
              <SearchOutlined style={{ color: '#666', fontSize: '24px' }} />
            </div>
            <div style={{ color: '#a6a6a6', fontSize: '16px', marginBottom: '8px' }}>
              No Expert Advisors Connected
            </div>
            <div style={{ color: '#666', fontSize: '12px', textAlign: 'center', maxWidth: '300px' }}>
              Connect your MT5 terminal to start monitoring your trading systems
            </div>
          </div>
        ) : filteredEAs.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '300px',
            background: 'linear-gradient(135deg, rgba(255, 170, 68, 0.05) 0%, rgba(255, 170, 68, 0.02) 100%)',
            borderRadius: '12px',
            border: '2px dashed rgba(255, 170, 68, 0.2)'
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              background: 'linear-gradient(135deg, #FFAA44 0%, #FF8800 100%)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px'
            }}>
              <SearchOutlined style={{ color: '#000', fontSize: '20px' }} />
            </div>
            <div style={{ color: '#FFAA44', fontSize: '14px', marginBottom: '6px' }}>
              No Systems Match Filters
            </div>
            <div style={{ color: '#666', fontSize: '11px' }}>
              Try adjusting your search criteria
            </div>
          </div>
        ) : (
          <Row gutter={[16, 16]}>
            {filteredEAs.map((ea, index) => (
              <Col key={ea.magic_number} xs={24} sm={12} lg={8} xl={6}>
                <div 
                  style={{
                    animation: `fadeInUp 0.6s ease-out ${index * 0.1}s both`
                  }}
                >
                  {showCharts ? (
                    <EACardWithChart 
                      ea={ea}
                      showChart={true}
                      chartHeight={60}
                      onPause={handlePauseEA}
                      onResume={handleResumeEA}
                      onConfigure={handleConfigureEA}
                    />
                  ) : (
                    <SoldierEAPanel eaData={ea} />
                  )}
                </div>
              </Col>
            ))}
          </Row>
        )}
      </div>
    </div>
  );
};

export default EAGridView;