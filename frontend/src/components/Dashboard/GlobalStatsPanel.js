import { useState, useEffect } from 'react';
import { Row, Col, Progress, Divider } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, DollarOutlined, TrophyOutlined, RiseOutlined, FallOutlined, LineChartOutlined, BarChartOutlined } from '@ant-design/icons';
import ModernSkeleton from '../Common/ModernSkeleton';
import MiniChart from '../Charts/MiniChart';
import chartService from '../../services/chartService';

const GlobalStatsPanel = ({ data, filteredData = [], viewMode = 'summary' }) => {
  const [marketData, setMarketData] = useState({});
  const [loadingMarketData, setLoadingMarketData] = useState(true);

  // Major currency pairs to display
  const majorPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD'];

  useEffect(() => {
    const fetchMarketData = async () => {
      setLoadingMarketData(true);
      try {
        const chartData = await chartService.getMultipleChartData(majorPairs, '1H', 20);
        setMarketData(chartData);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
      } finally {
        setLoadingMarketData(false);
      }
    };

    fetchMarketData();

    // Refresh market data every 5 minutes
    const interval = setInterval(fetchMarketData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (!data) {
    return (
      <ModernSkeleton type="stats" loading={true} />
    );
  }

  const {
    totalPnL = 0,
    totalDrawdown = 0,
    winRate = 0,
    totalTrades = 0,
    totalEAs = 0,
    dailyPnL = 0,
    weeklyPnL = 0,
    monthlyPnL = 0,
    avgProfitFactor = 0,
    totalVolume = 0
  } = data;

  // Calculate filtered stats if filteredData is provided
  const filteredStats = filteredData.length > 0 ? {
    filteredCount: filteredData.length,
    filteredActive: filteredData.filter(ea => (ea.openPositions || ea.open_positions) > 0).length,
    filteredPnL: filteredData.reduce((sum, ea) => sum + (ea.currentProfit || ea.current_profit || 0), 0),
    filteredPositions: filteredData.reduce((sum, ea) => sum + (ea.openPositions || ea.open_positions || 0), 0)
  } : null;



  return (
    <div className="advanced-global-stats-panel" style={{ position: 'relative' }}>
      {/* Header with Live Indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '24px',
        paddingBottom: '12px',
        borderBottom: '2px solid #1A1A1A'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            background: 'linear-gradient(135deg, #00FF88 0%, #00D4FF 100%)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(0, 255, 136, 0.3)'
          }}>
            <BarChartOutlined style={{ color: '#000', fontSize: '18px' }} />
          </div>
          <div>
            <h2 style={{
              color: '#E0E0E0',
              fontSize: '18px',
              fontWeight: '700',
              margin: 0,
              textTransform: 'uppercase',
              letterSpacing: '0.8px'
            }}>
              PORTFOLIO ANALYTICS
            </h2>
            <div style={{
              fontSize: '11px',
              color: '#666',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginTop: '2px'
            }}>
              Real-time Performance Dashboard
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 10px',
            backgroundColor: 'rgba(0, 255, 136, 0.1)',
            borderRadius: '6px',
            border: '1px solid rgba(0, 255, 136, 0.2)'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#00FF88',
              animation: 'pulse 2s infinite'
            }} />
            <span style={{ color: '#00FF88', fontSize: '11px', fontWeight: '600' }}>
              LIVE DATA
            </span>
          </div>
          <div style={{
            color: '#666',
            fontSize: '11px',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            Last Update: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Enhanced Main Statistics Row */}
      <Row gutter={[16, 16]}>
        <Col span={viewMode === 'detailed' ? 4 : 6}>
          <div className="advanced-stat-card" style={{
            background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 255, 136, 0.05) 100%)',
            border: '1px solid rgba(0, 255, 136, 0.2)',
            borderRadius: '8px',
            padding: '16px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '2px',
              background: 'linear-gradient(90deg, #00FF88, #00D4FF)',
              animation: 'shimmer 3s infinite'
            }} />
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <DollarOutlined style={{ color: '#00FF88', fontSize: '16px' }} />
              <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>TOTAL P&L</span>
            </div>
            <div style={{
              color: (filteredStats ? filteredStats.filteredPnL : totalPnL) >= 0 ? '#00FF88' : '#FF4466',
              fontSize: '24px',
              fontWeight: '700',
              fontFamily: '"JetBrains Mono", monospace'
            }}>
              ${(filteredStats ? filteredStats.filteredPnL : totalPnL).toFixed(2)}
            </div>
            <div style={{
              fontSize: '10px',
              color: '#666',
              marginTop: '4px'
            }}>
              {(filteredStats ? filteredStats.filteredPnL : totalPnL) >= 0 ? '↗' : '↘'} Portfolio Value
            </div>
          </div>
        </Col>

        <Col span={viewMode === 'detailed' ? 4 : 6}>
          <div className="advanced-stat-card" style={{
            background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%)',
            border: '1px solid rgba(0, 212, 255, 0.2)',
            borderRadius: '8px',
            padding: '16px',
            position: 'relative'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              {dailyPnL >= 0 ? <RiseOutlined style={{ color: '#00D4FF', fontSize: '16px' }} /> : <FallOutlined style={{ color: '#00D4FF', fontSize: '16px' }} />}
              <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>DAILY P&L</span>
            </div>
            <div style={{
              color: dailyPnL >= 0 ? '#00D4FF' : '#FF4466',
              fontSize: '24px',
              fontWeight: '700',
              fontFamily: '"JetBrains Mono", monospace'
            }}>
              ${dailyPnL.toFixed(2)}
            </div>
            <div style={{
              fontSize: '10px',
              color: '#666',
              marginTop: '4px'
            }}>
              Today's Performance
            </div>
          </div>
        </Col>

        <Col span={viewMode === 'detailed' ? 4 : 6}>
          <div className="advanced-stat-card" style={{
            background: 'linear-gradient(135deg, rgba(255, 170, 68, 0.1) 0%, rgba(255, 170, 68, 0.05) 100%)',
            border: '1px solid rgba(255, 170, 68, 0.2)',
            borderRadius: '8px',
            padding: '16px',
            position: 'relative'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              {weeklyPnL >= 0 ? <ArrowUpOutlined style={{ color: '#FFAA44', fontSize: '16px' }} /> : <ArrowDownOutlined style={{ color: '#FFAA44', fontSize: '16px' }} />}
              <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>WEEKLY P&L</span>
            </div>
            <div style={{
              color: weeklyPnL >= 0 ? '#FFAA44' : '#FF4466',
              fontSize: '24px',
              fontWeight: '700',
              fontFamily: '"JetBrains Mono", monospace'
            }}>
              ${weeklyPnL.toFixed(2)}
            </div>
            <div style={{
              fontSize: '10px',
              color: '#666',
              marginTop: '4px'
            }}>
              7-Day Performance
            </div>
          </div>
        </Col>

        {viewMode === 'detailed' && (
          <Col span={4}>
            <div className="advanced-stat-card" style={{
              background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(82, 196, 26, 0.05) 100%)',
              border: '1px solid rgba(82, 196, 26, 0.2)',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px'
              }}>
                {monthlyPnL >= 0 ? <ArrowUpOutlined style={{ color: '#52C41A', fontSize: '16px' }} /> : <ArrowDownOutlined style={{ color: '#52C41A', fontSize: '16px' }} />}
                <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>MONTHLY</span>
              </div>
              <div style={{
                color: monthlyPnL >= 0 ? '#52C41A' : '#FF4466',
                fontSize: '24px',
                fontWeight: '700',
                fontFamily: '"JetBrains Mono", monospace'
              }}>
                ${monthlyPnL.toFixed(2)}
              </div>
              <div style={{
                fontSize: '10px',
                color: '#666',
                marginTop: '4px'
              }}>
                30-Day Performance
              </div>
            </div>
          </Col>
        )}

        <Col span={viewMode === 'detailed' ? 4 : 6}>
          <div className="advanced-stat-card" style={{
            background: 'linear-gradient(135deg, rgba(255, 68, 102, 0.1) 0%, rgba(255, 68, 102, 0.05) 100%)',
            border: '1px solid rgba(255, 68, 102, 0.2)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <TrophyOutlined style={{ color: '#FF4466', fontSize: '16px' }} />
              <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>TRADES</span>
            </div>
            <div style={{
              color: '#FF4466',
              fontSize: '24px',
              fontWeight: '700',
              fontFamily: '"JetBrains Mono", monospace'
            }}>
              {totalTrades.toLocaleString()}
            </div>
            <div style={{
              fontSize: '10px',
              color: '#666',
              marginTop: '4px'
            }}>
              Total Executed
            </div>
          </div>
        </Col>

        {viewMode === 'detailed' && (
          <Col span={4}>
            <div className="advanced-stat-card" style={{
              background: 'linear-gradient(135deg, rgba(138, 43, 226, 0.1) 0%, rgba(138, 43, 226, 0.05) 100%)',
              border: '1px solid rgba(138, 43, 226, 0.2)',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px'
              }}>
                <LineChartOutlined style={{ color: '#8A2BE2', fontSize: '16px' }} />
                <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>AVG PF</span>
              </div>
              <div style={{
                color: avgProfitFactor >= 1.5 ? '#52C41A' : avgProfitFactor >= 1.0 ? '#FFAA44' : '#FF4466',
                fontSize: '24px',
                fontWeight: '700',
                fontFamily: '"JetBrains Mono", monospace'
              }}>
                {avgProfitFactor.toFixed(2)}
              </div>
              <div style={{
                fontSize: '10px',
                color: '#666',
                marginTop: '4px'
              }}>
                Profit Factor
              </div>
            </div>
          </Col>
        )}
      </Row>

      {/* Performance Indicators Row */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={viewMode === 'detailed' ? 8 : 12}>
          <div>
            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
              <span>Win Rate</span>
              <span style={{ fontWeight: 'bold' }}>{winRate.toFixed(1)}%</span>
            </div>
            <Progress
              percent={winRate}
              strokeColor={winRate >= 60 ? '#52c41a' : winRate >= 40 ? '#faad14' : '#ff4d4f'}
              showInfo={false}
            />
          </div>
        </Col>
        <Col span={viewMode === 'detailed' ? 8 : 12}>
          <div>
            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
              <span>Max Drawdown</span>
              <span style={{ fontWeight: 'bold', color: '#ff4d4f' }}>{totalDrawdown.toFixed(1)}%</span>
            </div>
            <Progress
              percent={Math.min(totalDrawdown, 100)}
              strokeColor='#ff4d4f'
              showInfo={false}
            />
          </div>
        </Col>
        {viewMode === 'detailed' && (
          <Col span={8}>
            <div>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>Volume</span>
                <span style={{ fontWeight: 'bold' }}>{(totalVolume || 0).toFixed(2)} lots</span>
              </div>
              <Progress
                percent={Math.min((totalVolume || 0) / 100 * 100, 100)}
                strokeColor='#1890ff'
                showInfo={false}
              />
            </div>
          </Col>
        )}
      </Row>

      {/* Market Overview Section */}
      <Divider style={{ margin: '16px 0' }} />
      <div style={{ marginBottom: 16 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: 12,
          fontSize: '14px',
          fontWeight: 'bold',
          color: '#CCCCCC'
        }}>
          <LineChartOutlined />
          <span>Market Overview</span>
        </div>

        {loadingMarketData ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
            Loading market data...
          </div>
        ) : (
          <Row gutter={[12, 12]}>
            {majorPairs.map(symbol => {
              const symbolData = marketData[symbol];
              if (!symbolData) return null;

              const priceChange = symbolData.price_change || 0;
              const currentPrice = symbolData.current_price || 0;
              const chartColor = priceChange >= 0 ? '#00C851' : '#FF4444';

              return (
                <Col key={symbol} span={4}>
                  <div style={{
                    padding: '8px',
                    backgroundColor: '#0F0F0F',
                    borderRadius: '6px',
                    border: '1px solid #1A1A1A',
                    textAlign: 'center'
                  }}>
                    <div style={{
                      fontSize: '11px',
                      fontWeight: '600',
                      color: '#CCCCCC',
                      marginBottom: '4px',
                      fontFamily: '"JetBrains Mono", monospace'
                    }}>
                      {symbol}
                    </div>

                    <div style={{
                      marginBottom: '6px',
                      height: '30px',
                      width: '100%'
                    }}>
                      <MiniChart
                        data={symbolData.data || []}
                        width={80}
                        height={30}
                        color={chartColor}
                        strokeWidth={1.5}
                        responsive={true}
                      />
                    </div>

                    <div style={{
                      fontSize: '10px',
                      fontWeight: '700',
                      color: '#CCCCCC',
                      fontFamily: '"JetBrains Mono", monospace'
                    }}>
                      {currentPrice.toFixed(symbol === 'USDJPY' ? 2 : 5)}
                    </div>

                    <div style={{
                      fontSize: '9px',
                      color: chartColor,
                      fontWeight: '600',
                      fontFamily: '"JetBrains Mono", monospace'
                    }}>
                      {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(symbol === 'USDJPY' ? 2 : 5)}
                    </div>
                  </div>
                </Col>
              );
            })}
          </Row>
        )}
      </div>

      {/* Filtered Stats Display */}
      {filteredStats && filteredStats.filteredCount !== totalEAs && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <div style={{
            padding: 12,
            background: 'rgba(24, 144, 255, 0.1)',
            borderRadius: 4,
            border: '1px solid rgba(24, 144, 255, 0.2)'
          }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: 8, color: '#1890ff' }}>
              Filtered View Statistics:
            </div>
            <Row gutter={16}>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
                    {filteredStats.filteredCount}
                  </div>
                  <div style={{ fontSize: '11px', color: '#a6a6a6' }}>EAs Shown</div>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#52c41a' }}>
                    {filteredStats.filteredActive}
                  </div>
                  <div style={{ fontSize: '11px', color: '#a6a6a6' }}>Running</div>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    fontSize: '18px',
                    fontWeight: 'bold',
                    color: filteredStats.filteredPnL >= 0 ? '#3f8600' : '#cf1322'
                  }}>
                    ${filteredStats.filteredPnL.toFixed(2)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#a6a6a6' }}>Filtered P&L</div>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fa8c16' }}>
                    {filteredStats.filteredPositions}
                  </div>
                  <div style={{ fontSize: '11px', color: '#a6a6a6' }}>Positions</div>
                </div>
              </Col>
            </Row>
          </div>
        </>
      )}
    </div>
  );
};

export default GlobalStatsPanel;