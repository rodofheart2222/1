import React, { useEffect, useState } from 'react';
import { Layout, Row, Col, Spin, Alert, Switch, Space } from 'antd';
import {
  DashboardOutlined,
  ControlOutlined,
  DisconnectOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  GlobalOutlined,
  RobotOutlined,
  AlertOutlined,
  AimOutlined,
  MonitorOutlined,
  DatabaseOutlined,
  ApiOutlined,
  SecurityScanOutlined,
  RadarChartOutlined,
  TrophyOutlined,
  RocketOutlined,
  ConsoleSqlOutlined,
  ClusterOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  LineChartOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';
import { useDashboard } from '../../context/DashboardContext';
import dashboardService from '../../services/dashboardService';
import webSocketService from '../../services/webSocketService';
import GlobalStatsPanel from './GlobalStatsPanel';
import EAGridView from './EAGridView';
import NewsEventPanel from './NewsEventPanel';
import CommandCenter from './CommandCenter';
import COCDashboard from './COCDashboard';
import ExpertsPanel from './ExpertsPanel';
import ConnectionStatus from '../Common/ConnectionStatus';
import FloatingActionButton from '../Common/FloatingActionButton';
import PerformanceMonitor from '../Common/PerformanceMonitor';
import './Dashboard.css';

const { Content } = Layout;

const Dashboard = ({ dashboardMode = 'soldier', isTransitioning = false }) => {
  const { state, actions } = useDashboard();
  const {
    connected,
    connecting,
    connectionError,
    eaData,
    globalStats,
    newsEvents,
    eaDataLoading
  } = state;


  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [animationClass, setAnimationClass] = useState('');
  const [displayMode, setDisplayMode] = useState(dashboardMode);

  // Handle mode transitions with proper animation timing
  useEffect(() => {
    if (isTransitioning) {
      // Start fade out animation
      setAnimationClass('fade-out');

      // After fade out completes, change the display mode and start fade in
      setTimeout(() => {
        setDisplayMode(dashboardMode);
        setAnimationClass('fade-in');

        // Clear animation class after fade in completes
        setTimeout(() => {
          setAnimationClass('');
        }, 400);
      }, 200);
    } else {
      // If not transitioning, sync immediately
      setDisplayMode(dashboardMode);
      setAnimationClass('');
    }
  }, [isTransitioning, dashboardMode]);

  // Market data is now handled by individual components using chartService

  // News data comes from newsEvents state

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);





  useEffect(() => {
    // Initialize dashboard
    initializeDashboard();

    // Safety timeout to ensure we don't get stuck in connecting state
    const connectingTimeout = setTimeout(() => {
      if (connecting) {
        console.warn('️ Dashboard initialization timeout - forcing completion');
        actions.setConnecting(false);
      }
    }, 10000); // 10 second timeout

    // Cleanup on unmount
    return () => {
      clearTimeout(connectingTimeout);
      dashboardService.stopPolling();
      webSocketService.disconnect();
      if (window.electronAPI) {
        window.electronAPI.removeWebSocketListeners();
      }
    };
  }, []);

  // Quick action handlers
  const handleRefresh = () => {
    initializeDashboard();
  };

  const handleSettings = () => {
    // TODO: Open settings modal
    console.log('Settings clicked');
  };

  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  const handleDebug = async () => {
    setShowPerformanceMonitor(!showPerformanceMonitor);
    console.log('Debug info:', { state, connected, eaData: eaData?.length });

    // Run connection test
    try {
      const { runConnectionTest } = await import('../../utils/connectionTest');
      const results = await runConnectionTest();
      console.log('Connection test results:', results);

      // Test WebSocket price updates
      const { testWebSocketPrices } = await import('../../utils/testWebSocketPrices');
      const priceTestResults = await testWebSocketPrices();
      console.log('WebSocket price test results:', priceTestResults);

    } catch (error) {
      console.error('Connection test failed:', error);
    }
  };

  const handleHelp = () => {
    // TODO: Open help documentation
    window.open('/docs', '_blank');
  };

  const initializeDashboard = async () => {
    try {
      console.log('🚀 Initializing dashboard...');
      actions.setConnecting(true);
      actions.setConnectionError(null);

      // Initialize dashboard service with actions
      dashboardService.initialize(actions);

      // Check backend connectivity first
      console.log('🔍 Checking backend connectivity...');
      const isConnected = await dashboardService.checkConnectivity();

      if (isConnected) {
        console.log('✅ Backend API is reachable');
        actions.setConnectionStatus(true);

        // Load initial data
        console.log('📊 Loading initial data...');
        await dashboardService.fetchAllData();

      } else {
        console.warn('⚠️ Backend API is not reachable - using fallback');
        actions.setConnectionStatus(false);

        // Set minimal fallback data
        actions.setEAData([]);
        actions.setGlobalStats({
          totalPnL: 0,
          totalDrawdown: 0,
          winRate: 0,
          totalTrades: 0,
          activeEAs: 0,
          totalEAs: 0,
          dailyPnL: 0,
          weeklyPnL: 0,
          monthlyPnL: 0,
          avgProfitFactor: 0,
          totalVolume: 0
        });
        actions.setNewsEvents([]);
      }

      // Set up WebSocket service event handlers
      setupWebSocketService();

      // Try to connect to WebSocket server for real-time updates
      try {
        console.log('🔌 Connecting to WebSocket...');
        await connectWebSocket();
        console.log('✅ WebSocket connected successfully');
      } catch (error) {
        console.warn('⚠️ WebSocket connection failed:', error.message);
        // Don't fail initialization due to WebSocket issues
      }

      // Start data polling as fallback/supplement
      const pollingInterval = isConnected ? 10000 : 30000;
      console.log(`⏱️ Starting data polling (${pollingInterval}ms interval)`);
      dashboardService.startPolling(pollingInterval);

    } catch (err) {
      console.error('❌ Dashboard initialization error:', err);
      actions.setConnectionError(`Initialization failed: ${err.message}`);
    } finally {
      actions.setConnecting(false);
      console.log('✅ Dashboard initialization complete');
    }
  };

  const setupWebSocketService = () => {
    // Set up WebSocket service event handlers
    webSocketService.onConnectionChange = (isConnected) => {
      console.log(` WebSocket connection change: ${isConnected ? 'Connected' : 'Disconnected'}`);
      actions.setConnectionStatus(isConnected);
      if (isConnected) {
        actions.setConnectionError(null);
      }
    };

    webSocketService.onMessage = (message) => {
      // Use dashboard service to handle message updates
      dashboardService.handleWebSocketUpdate(message);
    };

    webSocketService.onError = (error) => {
      console.error('WebSocket error:', error);
      const errorMessage = error?.message || 'WebSocket connection failed';

      // Only set connection error if it's a critical error, not just disconnection
      if (!errorMessage.includes('disconnected') && !errorMessage.includes('closed')) {
        const helpfulMessage = `${errorMessage}

 Troubleshooting Steps:
1. Ensure the WebSocket server is running:
   → cd backend && python start_websocket.py
   
2. Check if port 8765 is available:
   → The WebSocket server needs port 8765
   
3. Run system diagnostics:
   → cd backend && python diagnose_system.py
   
4. See SYSTEM_STARTUP_GUIDE.md for detailed instructions`;

        actions.setConnectionError(helpfulMessage);
      }
    };
  };

  const connectWebSocket = async () => {
    try {
      await webSocketService.connect(process.env.REACT_APP_WS_URL || 'ws://127.0.0.1:8765');

      // Manually check and update connection status after successful connection
      const status = webSocketService.getConnectionStatus();
      if (status.isConnected) {
        actions.setConnectionStatus(true);
        console.log(' WebSocket connection confirmed and status updated');
      }

      // Subscribe to relevant message types
      webSocketService.subscribe('ea_update', (data) => {
        actions.updateEAData(data);
      });

      webSocketService.subscribe('portfolio_update', (data) => {
        actions.setGlobalStats(data);
      });

      webSocketService.subscribe('news_update', (data) => {
        actions.setNewsEvents(data);
      });

      webSocketService.subscribe('command_update', (data) => {
        actions.updateCommand(data);
      });

      // Subscribe to price updates channel
      console.log('📈 Subscribing to price_updates channel...');
      webSocketService.sendMessage({
        type: 'subscribe',
        data: {
          channels: ['price_updates']
        }
      });

    } catch (error) {
      console.warn('WebSocket connection failed, continuing with HTTP polling only:', error);
      actions.setConnectionStatus(false);
      // Don't throw - continue with polling fallback
    }
  };

  // Debug logging
  console.log('Dashboard render state:', { connecting, connectionError, connected, eaData: eaData?.length });

  // Force show dashboard after 3 seconds if still connecting
  useEffect(() => {
    const forceShowTimeout = setTimeout(() => {
      if (connecting) {
        console.warn('⚠️ Forcing dashboard to show - was stuck in connecting state');
        actions.setConnecting(false);
        // Set some default data to ensure dashboard renders
        if (!eaData || eaData.length === 0) {
          console.log('📊 Setting fallback EA data');
          actions.setEAData([]);
        }
      }
    }, 3000); // Reduced to 3 seconds

    return () => clearTimeout(forceShowTimeout);
  }, [connecting, actions, eaData]);

  if (connecting) {
    return (
      <div className="dashboard-loading">
        <div className="loading-container glass-optimized">
          <div className="pulse-glow">
            <Spin size="large" />
          </div>
          <div className="loading-text">
            <h3 className="modern-title">Connecting to Backend</h3>
            <p className="modern-subtitle">Establishing connection to MT5 trading system...</p>
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div style={{ marginTop: '20px', fontSize: '12px', color: '#888' }}>
              <div>API: {process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'}</div>
              <div>WebSocket: {process.env.REACT_APP_WS_URL || 'ws://127.0.0.1:8765'}</div>
              <div style={{ marginTop: '10px' }}>
                If this takes too long, the dashboard will load with fallback data.
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (connectionError) {
    return (
      <div className="dashboard-error">
        <div className="error-container glass-optimized">
          <div className="error-icon">
            <DisconnectOutlined style={{ fontSize: '48px', color: '#ff4d4f' }} />
          </div>
          <h3 className="modern-title" style={{ color: '#ff4d4f', marginBottom: '16px' }}>
            Connection Error
          </h3>
          <div className="error-description">
            <pre style={{
              whiteSpace: 'pre-wrap',
              color: '#a6a6a6',
              fontSize: '13px',
              lineHeight: '1.6',
              marginBottom: '24px',
              background: 'rgba(255, 77, 79, 0.15)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 77, 79, 0.3)',
              boxShadow: '0 4px 15px rgba(255, 77, 79, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
            }}>
              {connectionError}
            </pre>
          </div>
          <button
            className="glass-button-primary"
            onClick={initializeDashboard}
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Fallback render to ensure something always shows
  console.log(' Rendering dashboard with state:', { connecting, connectionError, connected });

  return (
    <div className="dashboard" style={{
      minHeight: '100vh',
      backgroundColor: '#0A0A0A', // Deeper black for serious tone
      color: '#E0E0E0', // Softer light gray for better theme compatibility
      position: 'relative',
      fontFamily: '"Inter", "Segoe UI", system-ui, sans-serif', // More professional font
      letterSpacing: '0.01em'
    }}>






      <div style={{
        padding: '32px',
        paddingTop: '16px', // Reduced top padding since header is now in ticker bar
        minHeight: 'calc(100vh - 60px)', // Account for ticker bar (28px) + advanced intelligence header (32px)
        backgroundColor: '#0A0A0A'
      }}>
        <div className="dashboard-mode-container">
          <div className={`dashboard-mode-content ${animationClass}`}>
            {displayMode === 'coc' ? (
              <div style={{
                backgroundColor: '#111111',
                border: '1px solid #1A1A1A',
                borderRadius: '8px',
                padding: '32px',
                minHeight: '600px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  marginBottom: '32px',
                  paddingBottom: '16px',
                  borderBottom: '2px solid #1A1A1A'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    background: 'linear-gradient(135deg, #1565C0 0%, #0D47A1 100%)',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 6px 16px rgba(21, 101, 192, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                  }}>
                    <AimOutlined style={{ color: '#E0E0E0', fontSize: '24px' }} />
                  </div>
                  <div>
                    <h2 style={{
                      color: '#E0E0E0',
                      fontSize: '24px',
                      fontWeight: '700',
                      margin: 0,
                      textTransform: 'uppercase',
                      letterSpacing: '1px'
                    }}>
                      COMMAND CENTER
                    </h2>
                    <div style={{
                      fontSize: '12px',
                      color: '#a6a6a6',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      marginTop: '4px'
                    }}>
                      Strategic Portfolio Overview
                    </div>
                  </div>
                </div>
                <COCDashboard />
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* Global Statistics Panel */}
                <div style={{
                  backgroundColor: '#111111',
                  border: '1px solid #1A1A1A',
                  borderRadius: '8px',
                  padding: '24px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)'
                }}>

                  <GlobalStatsPanel
                    data={{
                      totalPnL: (eaData || []).reduce((sum, ea) => sum + (ea.current_profit || 0), 0),
                      totalDrawdown: (eaData || []).length > 0 ? (eaData || []).reduce((sum, ea) => sum + (ea.drawdown || 0), 0) / (eaData || []).length : 0,
                      winRate: (eaData || []).length > 0 ? (eaData || []).reduce((sum, ea) => sum + (ea.win_rate || 0), 0) / (eaData || []).length : 0,
                      totalTrades: (eaData || []).reduce((sum, ea) => sum + (ea.total_trades || 0), 0),
                      activeEAs: (eaData || []).filter(ea => (ea.open_positions || 0) > 0).length,
                      totalEAs: (eaData || []).length,
                      dailyPnL: (eaData || []).reduce((sum, ea) => sum + (ea.daily_profit || 0), 0),
                      weeklyPnL: (eaData || []).reduce((sum, ea) => sum + (ea.weekly_profit || 0), 0),
                      monthlyPnL: (eaData || []).reduce((sum, ea) => sum + (ea.current_profit || 0), 0),
                      avgProfitFactor: (eaData || []).length > 0 ? (eaData || []).reduce((sum, ea) => sum + (ea.profit_factor || 0), 0) / (eaData || []).length : 0,
                      totalVolume: (eaData || []).reduce((sum, ea) => sum + (ea.volume || 0), 0)
                    }}
                    filteredData={eaData || []}
                  />
                </div>

                {/* Main Content Area */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 380px',
                  gap: '24px'
                }}>
                  {/* EA Grid */}
                  <div style={{
                    backgroundColor: '#111111',
                    border: '1px solid #1A1A1A',
                    borderRadius: '8px',
                    padding: '24px',
                    minHeight: '600px',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '20px',
                      paddingBottom: '12px',
                      borderBottom: '1px solid #1A1A1A'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <h3 style={{
                          color: '#E0E0E0',
                          fontSize: '16px',
                          fontWeight: '700',
                          margin: 0,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px'
                        }}>
                          EXPERT ADVISORS
                        </h3>
                      </div>

                    </div>
                    <EAGridView eaData={eaData || []} />
                  </div>

                  {/* Side Panel */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{
                      backgroundColor: '#111111',
                      border: '1px solid #1A1A1A',
                      borderRadius: '8px',
                      padding: '20px',
                      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        marginBottom: '16px',
                        paddingBottom: '10px',
                        borderBottom: '1px solid #1A1A1A'
                      }}>
                        <h3 style={{
                          color: '#E0E0E0',
                          fontSize: '14px',
                          fontWeight: '700',
                          margin: 0,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px'
                        }}>
                          MARKET NEWS
                        </h3>
                      </div>
                      <NewsEventPanel events={newsEvents || []} />
                    </div>
                    <ExpertsPanel />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Status */}
      <div style={{
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        background: 'linear-gradient(135deg, #111111 0%, #1A1A1A 100%)',
        border: '1px solid #333333',
        color: '#CCCCCC',
        padding: '18px',
        borderRadius: '8px',
        fontSize: '10px',
        maxWidth: '320px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        fontFamily: '"JetBrains Mono", "Consolas", monospace',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{
          marginBottom: '12px',
          color: '#1565C0',
          fontWeight: '700',
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <SecurityScanOutlined style={{ fontSize: '12px' }} />
          SYSTEM STATUS
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '9px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ApiOutlined style={{ fontSize: '10px', color: connecting ? '#FF9800' : '#2E7D32' }} />
            CONN: <span style={{ color: connecting ? '#FF9800' : '#2E7D32', fontWeight: '600' }}>
              {connecting ? 'INIT' : 'READY'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertOutlined style={{ fontSize: '10px', color: connectionError ? '#D32F2F' : '#2E7D32' }} />
            ERR: <span style={{ color: connectionError ? '#D32F2F' : '#2E7D32', fontWeight: '600' }}>
              {connectionError ? 'YES' : 'NO'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RobotOutlined style={{ fontSize: '10px', color: '#1565C0' }} />
            EAS: <span style={{ color: '#1565C0', fontWeight: '600' }}>{eaData?.length || 0}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RadarChartOutlined style={{ fontSize: '10px', color: '#1565C0' }} />
            MODE: <span style={{ color: '#1565C0', fontWeight: '600' }}>{dashboardMode.toUpperCase()}</span>
          </div>
        </div>
      </div>

      <FloatingActionButton
        onRefresh={handleRefresh}
        onSettings={handleSettings}
        onFullscreen={handleFullscreen}
        onDebug={handleDebug}
        onHelp={handleHelp}
      />
    </div>
  );
};

export default Dashboard;