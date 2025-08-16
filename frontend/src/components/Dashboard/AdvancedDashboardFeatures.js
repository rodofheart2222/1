import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Progress, Tag, Tooltip, Space } from 'antd';
import {
  ThunderboltOutlined,
  RadarChartOutlined,
  SecurityScanOutlined,
  MonitorOutlined,
  TrophyOutlined,
  RocketOutlined,
  AlertOutlined,
  LineChartOutlined,
  BarChartOutlined,
  DashboardOutlined,
  ApiOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  GlobalOutlined,
  AimOutlined,
  FireOutlined,
  StarOutlined,
  CrownOutlined
} from '@ant-design/icons';
import AdvancedChart from '../Charts/AdvancedChart';

const AdvancedDashboardFeatures = ({ eaData = [], marketData = {} }) => {
  const [realTimeMetrics, setRealTimeMetrics] = useState({
    systemHealth: 98,
    networkLatency: 12,
    executionSpeed: 0.8,
    riskLevel: 'MODERATE',
    marketSentiment: 'BULLISH',
    volatilityIndex: 65,
    correlationStrength: 0.73,
    diversificationScore: 85
  });

  const [performanceMetrics, setPerformanceMetrics] = useState({
    sharpeRatio: 1.85,
    sortinoRatio: 2.34,
    maxDrawdown: 8.5,
    calmarRatio: 0.92,
    profitFactor: 1.67,
    winRate: 68.5,
    avgWin: 125.50,
    avgLoss: -78.20,
    expectancy: 42.30
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRealTimeMetrics(prev => ({
        ...prev,
        systemHealth: Math.max(90, Math.min(100, prev.systemHealth + (Math.random() - 0.5) * 2)),
        networkLatency: Math.max(5, Math.min(50, prev.networkLatency + (Math.random() - 0.5) * 5)),
        executionSpeed: Math.max(0.1, Math.min(2.0, prev.executionSpeed + (Math.random() - 0.5) * 0.1)),
        volatilityIndex: Math.max(20, Math.min(100, prev.volatilityIndex + (Math.random() - 0.5) * 10))
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getHealthColor = (value) => {
    if (value >= 95) return '#00FF88';
    if (value >= 85) return '#FFAA44';
    return '#FF4466';
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'LOW': return '#00FF88';
      case 'MODERATE': return '#FFAA44';
      case 'HIGH': return '#FF4466';
      default: return '#666';
    }
  };

  return (
    <div className="advanced-dashboard-features">
      {/* Real-time System Monitoring */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  background: 'linear-gradient(135deg, #00FF88 0%, #00D4FF 100%)',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <MonitorOutlined style={{ color: '#000', fontSize: '16px' }} />
                </div>
                <span style={{ color: '#E0E0E0', fontSize: '16px', fontWeight: '700' }}>
                  REAL-TIME SYSTEM MONITORING
                </span>
                <div style={{
                  padding: '2px 8px',
                  background: 'linear-gradient(135deg, #00FF88 0%, #00D4FF 100%)',
                  borderRadius: '12px',
                  fontSize: '10px',
                  color: '#000',
                  fontWeight: '700'
                }}>
                  LIVE
                </div>
              </div>
            }
            style={{
              background: '#111111',
              border: '1px solid #1A1A1A',
              borderRadius: '8px'
            }}
          >
            <Row gutter={[16, 16]}>
              {/* System Health */}
              <Col span={6}>
                <div style={{
                  padding: '16px',
                  background: `linear-gradient(135deg, ${getHealthColor(realTimeMetrics.systemHealth)}15 0%, ${getHealthColor(realTimeMetrics.systemHealth)}05 100%)`,
                  borderRadius: '8px',
                  border: `1px solid ${getHealthColor(realTimeMetrics.systemHealth)}30`,
                  position: 'relative'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '12px'
                  }}>
                    <SecurityScanOutlined style={{ color: getHealthColor(realTimeMetrics.systemHealth), fontSize: '16px' }} />
                    <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>SYSTEM HEALTH</span>
                  </div>
                  <div style={{
                    color: getHealthColor(realTimeMetrics.systemHealth),
                    fontSize: '24px',
                    fontWeight: '700',
                    marginBottom: '8px'
                  }}>
                    {realTimeMetrics.systemHealth.toFixed(1)}%
                  </div>
                  <Progress
                    percent={realTimeMetrics.systemHealth}
                    strokeColor={getHealthColor(realTimeMetrics.systemHealth)}
                    showInfo={false}
                    size="small"
                  />
                </div>
              </Col>

              {/* Network Latency */}
              <Col span={6}>
                <div style={{
                  padding: '16px',
                  background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 212, 255, 0.05) 100%)',
                  borderRadius: '8px',
                  border: '1px solid rgba(0, 212, 255, 0.3)'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '12px'
                  }}>
                    <ApiOutlined style={{ color: '#00D4FF', fontSize: '16px' }} />
                    <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>LATENCY</span>
                  </div>
                  <div style={{
                    color: '#00D4FF',
                    fontSize: '24px',
                    fontWeight: '700',
                    marginBottom: '8px'
                  }}>
                    {realTimeMetrics.networkLatency.toFixed(0)}ms
                  </div>
                  <div style={{ color: '#666', fontSize: '10px' }}>
                    Network Response Time
                  </div>
                </div>
              </Col>

              {/* Execution Speed */}
              <Col span={6}>
                <div style={{
                  padding: '16px',
                  background: 'linear-gradient(135deg, rgba(255, 170, 68, 0.15) 0%, rgba(255, 170, 68, 0.05) 100%)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 170, 68, 0.3)'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '12px'
                  }}>
                    <ThunderboltOutlined style={{ color: '#FFAA44', fontSize: '16px' }} />
                    <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>EXECUTION</span>
                  </div>
                  <div style={{
                    color: '#FFAA44',
                    fontSize: '24px',
                    fontWeight: '700',
                    marginBottom: '8px'
                  }}>
                    {realTimeMetrics.executionSpeed.toFixed(1)}s
                  </div>
                  <div style={{ color: '#666', fontSize: '10px' }}>
                    Average Order Speed
                  </div>
                </div>
              </Col>

              {/* Risk Level */}
              <Col span={6}>
                <div style={{
                  padding: '16px',
                  background: `linear-gradient(135deg, ${getRiskColor(realTimeMetrics.riskLevel)}15 0%, ${getRiskColor(realTimeMetrics.riskLevel)}05 100%)`,
                  borderRadius: '8px',
                  border: `1px solid ${getRiskColor(realTimeMetrics.riskLevel)}30`
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '12px'
                  }}>
                    <AlertOutlined style={{ color: getRiskColor(realTimeMetrics.riskLevel), fontSize: '16px' }} />
                    <span style={{ color: '#CCCCCC', fontSize: '12px', fontWeight: '600' }}>RISK LEVEL</span>
                  </div>
                  <div style={{
                    color: getRiskColor(realTimeMetrics.riskLevel),
                    fontSize: '18px',
                    fontWeight: '700',
                    marginBottom: '8px'
                  }}>
                    {realTimeMetrics.riskLevel}
                  </div>
                  <div style={{ color: '#666', fontSize: '10px' }}>
                    Portfolio Exposure
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Advanced Performance Analytics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={16}>
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  background: 'linear-gradient(135deg, #FF4466 0%, #FFAA44 100%)',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <BarChartOutlined style={{ color: '#FFF', fontSize: '16px' }} />
                </div>
                <span style={{ color: '#E0E0E0', fontSize: '16px', fontWeight: '700' }}>
                  ADVANCED PERFORMANCE METRICS
                </span>
              </div>
            }
            style={{
              background: '#111111',
              border: '1px solid #1A1A1A',
              borderRadius: '8px'
            }}
          >
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div style={{
                    width: '60px',
                    height: '60px',
                    margin: '0 auto 12px',
                    background: 'conic-gradient(from 0deg, #00FF88 0%, #00FF88 68%, #333 68%, #333 100%)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative'
                  }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      background: '#111111',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <TrophyOutlined style={{ color: '#00FF88', fontSize: '16px' }} />
                    </div>
                  </div>
                  <div style={{ color: '#00FF88', fontSize: '20px', fontWeight: '700' }}>
                    {performanceMetrics.sharpeRatio}
                  </div>
                  <div style={{ color: '#CCCCCC', fontSize: '12px' }}>Sharpe Ratio</div>
                  <div style={{ color: '#666', fontSize: '10px' }}>Risk-adjusted return</div>
                </div>
              </Col>

              <Col span={8}>
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div style={{
                    width: '60px',
                    height: '60px',
                    margin: '0 auto 12px',
                    background: 'conic-gradient(from 0deg, #00D4FF 0%, #00D4FF 75%, #333 75%, #333 100%)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      background: '#111111',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <RocketOutlined style={{ color: '#00D4FF', fontSize: '16px' }} />
                    </div>
                  </div>
                  <div style={{ color: '#00D4FF', fontSize: '20px', fontWeight: '700' }}>
                    {performanceMetrics.sortinoRatio}
                  </div>
                  <div style={{ color: '#CCCCCC', fontSize: '12px' }}>Sortino Ratio</div>
                  <div style={{ color: '#666', fontSize: '10px' }}>Downside deviation</div>
                </div>
              </Col>

              <Col span={8}>
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div style={{
                    width: '60px',
                    height: '60px',
                    margin: '0 auto 12px',
                    background: 'conic-gradient(from 0deg, #FFAA44 0%, #FFAA44 60%, #333 60%, #333 100%)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      background: '#111111',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <StarOutlined style={{ color: '#FFAA44', fontSize: '16px' }} />
                    </div>
                  </div>
                  <div style={{ color: '#FFAA44', fontSize: '20px', fontWeight: '700' }}>
                    {performanceMetrics.calmarRatio}
                  </div>
                  <div style={{ color: '#CCCCCC', fontSize: '12px' }}>Calmar Ratio</div>
                  <div style={{ color: '#666', fontSize: '10px' }}>Return vs drawdown</div>
                </div>
              </Col>
            </Row>

            <div style={{
              marginTop: '20px',
              padding: '16px',
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.05)'
            }}>
              <Row gutter={[16, 8]}>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#52C41A', fontSize: '16px', fontWeight: '700' }}>
                      {performanceMetrics.profitFactor}
                    </div>
                    <div style={{ color: '#666', fontSize: '10px' }}>Profit Factor</div>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#1890FF', fontSize: '16px', fontWeight: '700' }}>
                      {performanceMetrics.winRate}%
                    </div>
                    <div style={{ color: '#666', fontSize: '10px' }}>Win Rate</div>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#00FF88', fontSize: '16px', fontWeight: '700' }}>
                      ${performanceMetrics.avgWin}
                    </div>
                    <div style={{ color: '#666', fontSize: '10px' }}>Avg Win</div>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#FF4466', fontSize: '16px', fontWeight: '700' }}>
                      ${performanceMetrics.avgLoss}
                    </div>
                    <div style={{ color: '#666', fontSize: '10px' }}>Avg Loss</div>
                  </div>
                </Col>
              </Row>
            </div>
          </Card>
        </Col>

        <Col span={8}>
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  background: 'linear-gradient(135deg, #8A2BE2 0%, #FF1493 100%)',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <RadarChartOutlined style={{ color: '#FFF', fontSize: '16px' }} />
                </div>
                <span style={{ color: '#E0E0E0', fontSize: '16px', fontWeight: '700' }}>
                  MARKET INTELLIGENCE
                </span>
              </div>
            }
            style={{
              background: '#111111',
              border: '1px solid #1A1A1A',
              borderRadius: '8px'
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Market Sentiment */}
              <div style={{
                padding: '12px',
                background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 255, 136, 0.05) 100%)',
                borderRadius: '6px',
                border: '1px solid rgba(0, 255, 136, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{ color: '#CCCCCC', fontSize: '12px' }}>Market Sentiment</span>
                  <Tag color="success">{realTimeMetrics.marketSentiment}</Tag>
                </div>
                <div style={{ color: '#00FF88', fontSize: '18px', fontWeight: '700' }}>
                  BULLISH MOMENTUM
                </div>
              </div>

              {/* Volatility Index */}
              <div style={{
                padding: '12px',
                background: 'linear-gradient(135deg, rgba(255, 170, 68, 0.1) 0%, rgba(255, 170, 68, 0.05) 100%)',
                borderRadius: '6px',
                border: '1px solid rgba(255, 170, 68, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{ color: '#CCCCCC', fontSize: '12px' }}>Volatility Index</span>
                  <span style={{ color: '#FFAA44', fontSize: '14px', fontWeight: '700' }}>
                    {realTimeMetrics.volatilityIndex.toFixed(0)}
                  </span>
                </div>
                <Progress
                  percent={realTimeMetrics.volatilityIndex}
                  strokeColor="#FFAA44"
                  showInfo={false}
                  size="small"
                />
              </div>

              {/* Correlation Strength */}
              <div style={{
                padding: '12px',
                background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%)',
                borderRadius: '6px',
                border: '1px solid rgba(0, 212, 255, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{ color: '#CCCCCC', fontSize: '12px' }}>Correlation</span>
                  <span style={{ color: '#00D4FF', fontSize: '14px', fontWeight: '700' }}>
                    {realTimeMetrics.correlationStrength.toFixed(2)}
                  </span>
                </div>
                <Progress
                  percent={realTimeMetrics.correlationStrength * 100}
                  strokeColor="#00D4FF"
                  showInfo={false}
                  size="small"
                />
              </div>

              {/* Diversification Score */}
              <div style={{
                padding: '12px',
                background: 'linear-gradient(135deg, rgba(138, 43, 226, 0.1) 0%, rgba(138, 43, 226, 0.05) 100%)',
                borderRadius: '6px',
                border: '1px solid rgba(138, 43, 226, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{ color: '#CCCCCC', fontSize: '12px' }}>Diversification</span>
                  <span style={{ color: '#8A2BE2', fontSize: '14px', fontWeight: '700' }}>
                    {realTimeMetrics.diversificationScore}%
                  </span>
                </div>
                <Progress
                  percent={realTimeMetrics.diversificationScore}
                  strokeColor="#8A2BE2"
                  showInfo={false}
                  size="small"
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Advanced Chart Showcase */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  background: 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <LineChartOutlined style={{ color: '#FFF', fontSize: '16px' }} />
                </div>
                <span style={{ color: '#E0E0E0', fontSize: '16px', fontWeight: '700' }}>
                  ADVANCED CHART ANALYTICS
                </span>
                <div style={{
                  padding: '2px 8px',
                  background: 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)',
                  borderRadius: '12px',
                  fontSize: '10px',
                  color: '#FFF',
                  fontWeight: '700'
                }}>
                  ENHANCED
                </div>
              </div>
            }
            style={{
              background: '#111111',
              border: '1px solid #1A1A1A',
              borderRadius: '8px'
            }}
          >
            <Row gutter={[16, 16]}>
              {['EURUSD', 'GBPUSD', 'USDJPY'].map((symbol, index) => (
                <Col key={symbol} span={8}>
                  <div style={{
                    background: 'rgba(0, 0, 0, 0.3)',
                    borderRadius: '8px',
                    padding: '16px',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '12px'
                    }}>
                      <span style={{ color: '#E0E0E0', fontSize: '14px', fontWeight: '700' }}>
                        {symbol}
                      </span>
                      <div style={{
                        padding: '2px 6px',
                        background: index === 0 ? 'rgba(0, 255, 136, 0.2)' : 
                                   index === 1 ? 'rgba(0, 212, 255, 0.2)' : 'rgba(255, 170, 68, 0.2)',
                        borderRadius: '3px',
                        fontSize: '9px',
                        color: index === 0 ? '#00FF88' : 
                               index === 1 ? '#00D4FF' : '#FFAA44',
                        fontWeight: '600'
                      }}>
                        LIVE
                      </div>
                    </div>
                    <AdvancedChart
                      symbol={symbol}
                      width={280}
                      height={180}
                      showControls={false}
                    />
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdvancedDashboardFeatures;