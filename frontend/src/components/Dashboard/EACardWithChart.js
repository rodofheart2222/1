import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, Tooltip, Spin } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  LineChartOutlined,
  DollarOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import MiniChart from '../Charts/MiniChart';
import chartService from '../../services/chartService';

const EACardWithChart = ({ 
  ea, 
  onPause, 
  onResume, 
  onConfigure, 
  showChart = true,
  chartHeight = 60 
}) => {
  const [chartData, setChartData] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [loadingChart, setLoadingChart] = useState(true);
  const [realTimePrice, setRealTimePrice] = useState(null);

  // Subscribe to price updates for this EA's symbol
  useEffect(() => {
    if (!ea?.symbol || !showChart) return;

    let unsubscribe;

    const subscribeToPrice = async () => {
      try {
        // Use direct MT5 price data via HTTP API polling
        console.log(`📈 Setting up MT5 price polling for ${ea.symbol}`);

      } catch (error) {
        console.error('Error subscribing to price updates:', error);
      }
    };

    subscribeToPrice();
    
    return () => {
      if (unsubscribe && typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [ea?.symbol, showChart]);

  // Load initial chart data
  useEffect(() => {
    if (!ea?.symbol || !showChart) return;

    const loadChartData = async () => {
      setLoadingChart(true);
      try {
        const data = await chartService.getChartData(ea.symbol, '1H', 30);
        
        if (data && data.data && Array.isArray(data.data)) {
          // Convert to mini chart format with validation
          const chartPoints = data.data
            .filter(point => point && typeof point.close === 'number' && !isNaN(point.close))
            .map(point => ({
              price: point.close,
              timestamp: point.timestamp
            }));
          
          console.log(`📊 Processed ${chartPoints.length} chart points for ${ea.symbol}:`, {
            symbol: ea.symbol,
            dataLength: data.data.length,
            validPoints: chartPoints.length,
            currentPrice: data.current_price,
            priceChange: data.price_change,
            firstPrice: chartPoints[0]?.price,
            lastPrice: chartPoints[chartPoints.length - 1]?.price
          });
          
          setChartData(chartPoints);
          setCurrentPrice(data.current_price);
          setPriceChange(data.price_change);
        } else {
          console.warn(`📊 Invalid chart data received for ${ea.symbol}:`, data);
        }
      } catch (error) {
        console.error('Error loading chart data:', error);
      } finally {
        setLoadingChart(false);
      }
    };

    loadChartData();
  }, [ea?.symbol, showChart]);

  const getStatusColor = () => {
    if (ea.is_paused) return '#FF6B6B';
    if (ea.current_profit > 0) return '#51CF66';
    if (ea.current_profit < 0) return '#FF8787';
    return '#868E96';
  };

  const getStatusText = () => {
    if (ea.is_paused) return 'Paused';
    if (ea.open_positions > 0) return 'Trading';
    return 'Active';
  };

  const getProfitColor = () => {
    return ea.current_profit >= 0 ? '#51CF66' : '#FF6B6B';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    const decimals = ea.symbol === 'XAUUSD' ? 2 : 5;
    return price.toFixed(decimals);
  };

  return (
    <Card
      size="small"
      style={{
        backgroundColor: '#1A1A1A',
        border: '1px solid #333333',
        borderRadius: '12px',
        marginBottom: '16px'
      }}
      bodyStyle={{ padding: '16px' }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px'
      }}>
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '4px'
          }}>
            <h4 style={{
              color: '#FFFFFF',
              margin: 0,
              fontSize: '16px',
              fontWeight: '600'
            }}>
              {ea.symbol}
            </h4>
            <Badge
              color={getStatusColor()}
              text={
                <span style={{ 
                  color: getStatusColor(),
                  fontSize: '11px',
                  fontWeight: '500'
                }}>
                  {getStatusText()}
                </span>
              }
            />
          </div>
          <div style={{
            color: '#888888',
            fontSize: '12px',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {ea.strategy_tag} • #{ea.magic_number}
          </div>
        </div>

        <div style={{
          display: 'flex',
          gap: '4px'
        }}>
          <Tooltip title={ea.is_paused ? "Resume EA" : "Pause EA"}>
            <Button
              type="text"
              size="small"
              icon={ea.is_paused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              onClick={() => ea.is_paused ? onResume?.(ea) : onPause?.(ea)}
              style={{
                color: ea.is_paused ? '#51CF66' : '#FF6B6B',
                border: 'none'
              }}
            />
          </Tooltip>
          <Tooltip title="Configure EA">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => onConfigure?.(ea)}
              style={{
                color: '#888888',
                border: 'none'
              }}
            />
          </Tooltip>
        </div>
      </div>

      {/* Price and Chart Section */}
      {showChart && (
        <div style={{
          backgroundColor: '#0F0F0F',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '12px',
          border: '1px solid #2A2A2A',
          minHeight: chartHeight + 60 // Ensure minimum height for content
        }}>
          {/* Price Header */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <LineChartOutlined style={{ color: '#666666', fontSize: '12px' }} />
              <span style={{
                color: '#CCCCCC',
                fontSize: '11px',
                fontWeight: '600'
              }}>
                Live Price
              </span>
            </div>
            
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              {priceChange >= 0 ? (
                <ArrowUpOutlined style={{ color: '#51CF66', fontSize: '10px' }} />
              ) : (
                <ArrowDownOutlined style={{ color: '#FF6B6B', fontSize: '10px' }} />
              )}
              <span style={{
                color: priceChange >= 0 ? '#51CF66' : '#FF6B6B',
                fontSize: '10px',
                fontWeight: '600',
                fontFamily: '"JetBrains Mono", monospace'
              }}>
                {priceChange >= 0 ? '+' : ''}{formatPrice(priceChange)}
              </span>
            </div>
          </div>

          {/* Current Price */}
          <div style={{
            color: '#FFFFFF',
            fontSize: '18px',
            fontWeight: '700',
            fontFamily: '"JetBrains Mono", monospace',
            marginBottom: '8px'
          }}>
            {formatPrice(realTimePrice?.price || currentPrice)}
          </div>

          {/* Mini Chart */}
          <div style={{
            height: chartHeight,
            width: '100%',
            position: 'relative'
          }}>
            {loadingChart ? (
              <div style={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Spin size="small" />
              </div>
            ) : (
              <MiniChart
                data={chartData}
                width={280}
                height={chartHeight}
                color={priceChange >= 0 ? '#51CF66' : '#FF6B6B'}
                strokeWidth={1.5}
                responsive={true}
              />
            )}
          </div>
        </div>
      )}

      {/* EA Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px'
      }}>
        {/* Profit */}
        <div style={{
          backgroundColor: '#0F0F0F',
          borderRadius: '6px',
          padding: '8px',
          border: '1px solid #2A2A2A'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            marginBottom: '4px'
          }}>
            <DollarOutlined style={{ color: '#666666', fontSize: '10px' }} />
            <span style={{
              color: '#888888',
              fontSize: '10px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Profit
            </span>
          </div>
          <div style={{
            color: getProfitColor(),
            fontSize: '14px',
            fontWeight: '700',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {formatCurrency(ea.current_profit)}
          </div>
        </div>

        {/* Positions */}
        <div style={{
          backgroundColor: '#0F0F0F',
          borderRadius: '6px',
          padding: '8px',
          border: '1px solid #2A2A2A'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            marginBottom: '4px'
          }}>
            <BarChartOutlined style={{ color: '#666666', fontSize: '10px' }} />
            <span style={{
              color: '#888888',
              fontSize: '10px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Positions
            </span>
          </div>
          <div style={{
            color: '#CCCCCC',
            fontSize: '14px',
            fontWeight: '700',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {ea.open_positions}
          </div>
        </div>
      </div>

      {/* Module Status */}
      {ea.module_status && Object.keys(ea.module_status).length > 0 && (
        <div style={{
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: '1px solid #2A2A2A'
        }}>
          <div style={{
            color: '#888888',
            fontSize: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '6px'
          }}>
            Modules
          </div>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '4px'
          }}>
            {Object.entries(ea.module_status).map(([module, status]) => (
              <Badge
                key={module}
                color={status === 'active' ? '#51CF66' : '#666666'}
                text={
                  <span style={{
                    fontSize: '9px',
                    color: status === 'active' ? '#51CF66' : '#666666'
                  }}>
                    {module}
                  </span>
                }
              />
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default EACardWithChart;