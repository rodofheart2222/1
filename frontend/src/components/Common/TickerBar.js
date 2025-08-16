import React, { useState, useEffect } from 'react';
import {
  RobotOutlined,
  AimOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import SmoothTicker from './SmoothTicker';
import chartService from '../../services/chartService';
import webSocketService from '../../services/webSocketService';
import './TickerBar.css';

const TickerBar = ({
  connected = false,
  eaData = [],
  dashboardMode = 'soldier',
  isTransitioning = false,
  onModeSwitch = () => { },
  newsEvents = []
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [marketData, setMarketData] = useState([]);
  const [hourlyBaseline, setHourlyBaseline] = useState({});
  const [dataSource, setDataSource] = useState('loading');

  // Define the symbols we want to show in the ticker
  const tickerSymbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD'];

  // Use real news data from props - no more mock data

  // Load initial market data and setup WebSocket connection
  useEffect(() => {
    const loadMarketData = async () => {
      try {
        console.log('📊 Loading initial market data for ticker...');
        
        // Get real ticker data from chart service
        const initialMarketData = await chartService.getTickerData(tickerSymbols);
        const baselinePrices = {};
        
        // Calculate baselines for hourly changes
        initialMarketData.forEach(item => {
          baselinePrices[item.symbol] = item.price - item.change;
        });
        
        setMarketData(initialMarketData);
        setHourlyBaseline(baselinePrices);
        setDataSource('loading');
        console.log('✅ Initial market data loaded, connecting to WebSocket...');
        
        // Connect to WebSocket for real-time MT5 data
        await setupWebSocketConnection();
        
      } catch (error) {
        console.error('❌ Failed to load initial market data:', error);
        setDataSource('error');
      }
    };

    loadMarketData();
  }, []);

  // Setup WebSocket connection for real-time MT5 price data
  const setupWebSocketConnection = async () => {
    try {
      console.log('🔌 Setting up WebSocket connection for ticker...');
      
      // Connect to WebSocket
      await webSocketService.connect();
      
      // Subscribe to price updates
      const unsubscribe = webSocketService.subscribe('price_update', (priceData) => {
        console.log('📈 Received price update for ticker:', Object.keys(priceData).length, 'symbols');
        updateMarketDataFromWebSocket(priceData);
      });
      
      // Subscribe to specific symbols for MT5 price data
      webSocketService.subscribeToPrices(tickerSymbols);
      
      setDataSource('mt5_websocket');
      console.log('✅ WebSocket connected and subscribed to price updates');
      
      // Cleanup function
      return () => {
        unsubscribe();
      };
      
    } catch (error) {
      console.error('❌ Failed to setup WebSocket connection:', error);
      setDataSource('fallback_demo');
    }
  };

  // Update market data from WebSocket price updates
  const updateMarketDataFromWebSocket = (priceData) => {
    try {
      const updatedMarketData = tickerSymbols.map(symbol => {
        const wsPrice = priceData[symbol];
        const existingData = marketData.find(item => item.symbol === symbol);
        
        if (wsPrice) {
          // Use WebSocket price data
          const currentPrice = wsPrice.price; // Mid price from WebSocket
          const baseline = hourlyBaseline[symbol] || currentPrice;
          const hourlyChange = currentPrice - baseline;
          const changePercent = baseline > 0 ? (hourlyChange / baseline) * 100 : 0;
          
          return {
            symbol,
            price: currentPrice,
            change: hourlyChange,
            changePercent: changePercent,
            volume: wsPrice.volume || 100000,
            source: 'mt5_websocket',
            bid: wsPrice.bid,
            ask: wsPrice.ask,
            spread: wsPrice.spread,
            timestamp: wsPrice.timestamp
          };
        } else if (existingData) {
          // Keep existing data if no WebSocket update
          return existingData;
        } else {
          // Fallback to chart service data
          const fallbackData = chartService.getTickerData([symbol])[0];
          return fallbackData || {
            symbol,
            price: 1.0000,
            change: 0,
            changePercent: 0,
            volume: 100000,
            source: 'fallback'
          };
        }
      });
      
      setMarketData(updatedMarketData);
      
      // Update chart service with latest prices for consistency
      const priceUpdates = {};
      updatedMarketData.forEach(item => {
        if (item.source === 'mt5_websocket') {
          priceUpdates[item.symbol] = item.price;
        }
      });
      
      if (Object.keys(priceUpdates).length > 0) {
        chartService.updatePrices(priceUpdates);
      }
      
    } catch (error) {
      console.error('❌ Error updating market data from WebSocket:', error);
    }
  };

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Cleanup WebSocket connection on unmount
  useEffect(() => {
    return () => {
      // WebSocket service handles its own cleanup
      console.log('🧹 TickerBar component unmounting, WebSocket cleanup handled by service');
    };
  }, []);

  // Enhanced scroll detection for ticker bar container
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const tickerContainer = document.querySelector('.ticker-bar-container');

      if (tickerContainer) {
        if (scrollY > 50) {
          tickerContainer.classList.add('scrolled');
        } else {
          tickerContainer.classList.remove('scrolled');
        }
      }
    };

    // Add scroll event listener
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Initial check
    handleScroll();

    // Cleanup
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const renderTickerItems = (keyPrefix = '') => [
    // Time container - Bloomberg style
    <div key={`time${keyPrefix}`} className="bloomberg-ticker-item" style={{
      padding: '0 12px',
      display: 'flex',
      alignItems: 'center',
      height: '28px',
      flexShrink: 0,
      whiteSpace: 'nowrap',
      borderRight: '1px solid #333333'
    }}>
      <span style={{
        fontSize: '11px',
        fontWeight: '700',
        color: '#FFFFFF',
        fontFamily: 'monospace',
        letterSpacing: '0.5px'
      }}>
        {currentTime.toLocaleTimeString('en-US', {
          hour12: false,
          timeZone: 'UTC'
        })} UTC
      </span>
    </div>,

    // Market data containers - Bloomberg style with SmoothTicker
    ...marketData.map((item, index) => (
      <div key={`market${keyPrefix}-${item.symbol}`} className="bloomberg-ticker-item" style={{
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        height: '28px',
        flexShrink: 0,
        whiteSpace: 'nowrap',
        borderRight: '1px solid #333333'
      }}>
        <span style={{
          fontSize: '11px',
          fontWeight: '700',
          color: '#FFFFFF',
          fontFamily: 'monospace',
          letterSpacing: '0.5px',
          minWidth: '50px'
        }}>
          {item.symbol}
        </span>
        <span style={{
          fontSize: '11px',
          fontWeight: '600',
          color: '#FFFFFF',
          fontFamily: 'monospace',
          minWidth: '60px'
        }}>
          <SmoothTicker
            targetValue={item.price}
            decimals={item.symbol === 'XAUUSD' ? 2 : item.symbol.includes('JPY') ? 2 : 5}
            showChangeIndicator={true}
          />
        </span>
        <span style={{
          fontSize: '10px',
          fontWeight: '600',
          color: item.change >= 0 ? '#00FF00' : '#FF0000',
          fontFamily: 'monospace',
          minWidth: '45px',
          backgroundColor: item.change >= 0 ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)',
          padding: '2px 4px',
          borderRadius: '2px'
        }}>
          {item.change >= 0 ? '▲' : '▼'} {item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(1)}%
        </span>
      </div>
    )),

    // News separator - Bloomberg style
    <div key={`news-sep${keyPrefix}`} className="bloomberg-ticker-item" style={{
      padding: '0 12px',
      display: 'flex',
      alignItems: 'center',
      height: '28px',
      flexShrink: 0,
      whiteSpace: 'nowrap',
      backgroundColor: '#FF6600',
      color: '#000000'
    }}>
      <span style={{
        fontSize: '10px',
        fontWeight: '800',
        color: '#000000',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        fontFamily: 'Arial, sans-serif'
      }}>
        BREAKING
      </span>
    </div>,

    // News items - Bloomberg style
    ...newsEvents.slice(0, 2).map((newsItem, index) => (
      <div key={`news${keyPrefix}-${newsItem.id}`} className="bloomberg-ticker-item" style={{
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        height: '28px',
        maxWidth: '500px',
        flexShrink: 0,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        borderRight: '1px solid #333333'
      }}>
        <span style={{
          fontSize: '9px',
          fontWeight: '700',
          color: '#FFFFFF',
          fontFamily: 'Arial, sans-serif',
          backgroundColor: newsItem.impact === 'high' ? '#FF0000' : newsItem.impact === 'medium' ? '#FF6600' : '#00AA00',
          padding: '2px 6px',
          borderRadius: '2px',
          minWidth: '35px',
          textAlign: 'center',
          textTransform: 'uppercase'
        }}>
          {newsItem.impact}
        </span>
        <span style={{
          fontSize: '9px',
          fontWeight: '600',
          color: '#FFFFFF',
          fontFamily: 'monospace'
        }}>
          {newsItem.time}
        </span>
        <span style={{
          fontSize: '10px',
          fontWeight: '400',
          color: '#FFFFFF',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          fontFamily: 'Arial, sans-serif'
        }}>
          {newsItem.headline}
        </span>
      </div>
    )),

    // Data source indicator - Bloomberg style
    <div key={`source${keyPrefix}`} className="bloomberg-ticker-item" style={{
      padding: '0 16px',
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      height: '28px',
      flexShrink: 0,
      whiteSpace: 'nowrap',
      backgroundColor: dataSource === 'mt5_websocket' ? '#00FF00' : 
                      dataSource === 'fallback_demo' ? '#FF6600' : 
                      dataSource === 'loading' ? '#0066FF' : '#666666',
      color: '#000000'
    }}>
      <span style={{
        fontSize: '10px',
        color: '#000000',
        fontWeight: '800',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        fontFamily: 'Arial, sans-serif'
      }}>
        {dataSource === 'mt5_websocket' ? 'MT5 LIVE' : 
         dataSource === 'fallback_demo' ? 'DEMO DATA' : 
         dataSource === 'loading' ? 'CONNECTING' : 'OFFLINE'}
      </span>
    </div>,

    // Market status - Bloomberg style
    <div key={`status${keyPrefix}`} className="bloomberg-ticker-item" style={{
      padding: '0 16px',
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      height: '28px',
      flexShrink: 0,
      whiteSpace: 'nowrap',
      backgroundColor: '#00AA00',
      color: '#000000'
    }}>
      <span style={{
        fontSize: '10px',
        color: '#000000',
        fontWeight: '800',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        fontFamily: 'Arial, sans-serif'
      }}>
        MARKETS UP
      </span>
    </div>
  ];

  return (
    <div className="ticker-bar-container">
      {/* Bloomberg Ticker Bar */}
      <div className="bloomberg-ticker-bar">
        <div className="ticker-container">
          {/* First set of ticker items */}
          <div className="ticker-content">
            {renderTickerItems()}
          </div>

          {/* Duplicate content for seamless loop */}
          <div className="ticker-content">
            {renderTickerItems('-dup')}
          </div>
        </div>
      </div>

      {/* Advanced Intelligence Header */}
      <div className="advanced-intelligence-header" style={{
        padding: '2px 10px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#111111',
        borderBottom: '1px solid #1A1A1A',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
        position: 'relative',
        zIndex: 999
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          {/* Main Title Section */}
          <div>
            <h1 style={{
              color: '#FFFFFF',
              fontSize: '28px',
              fontWeight: '800',
              margin: 0,
              textTransform: 'uppercase',
              letterSpacing: '2px',
              background: 'linear-gradient(135deg, #00d4ff 0%, #ffffff 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>

            </h1>
            <div style={{
              fontSize: '11px',
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              marginTop: '2px',
              fontWeight: '500'
            }}>
              Advanced Trading Intelligence • Real-time Market Control
            </div>
          </div>

          {/* Mode Selection */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '2px 12px',
              backgroundColor: '#1A1A1A',
              borderRadius: '6px',
              border: '1px solid #333333'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: connected ? '#4CAF50' : '#F44336',
                boxShadow: connected ? '0 0 8px rgba(76, 175, 80, 0.6)' : '0 0 8px rgba(244, 67, 54, 0.6)',
                animation: connected ? 'pulse 2s infinite' : 'none'
              }}></div>
              <span style={{
                fontWeight: '600',
                color: connected ? '#4CAF50' : '#F44336',
                fontSize: '11px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {connected ? 'NEURAL LINK ACTIVE' : 'NEURAL LINK DOWN'}
              </span>
            </div>

            <div style={{
              height: '24px',
              width: '1px',
              backgroundColor: '#333333'
            }}></div>

            <span style={{
              fontWeight: '500',
              color: '#FFFFFF',
              fontSize: '11px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              OPERATION MODE
            </span>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                onClick={() => onModeSwitch('soldier')}
                disabled={isTransitioning}
                className="glow-button"
                style={{
                  padding: '2px 12px',
                  fontSize: '11px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  backgroundColor: dashboardMode === 'soldier' ? '#FFFFFF' : '#1A1A1A',
                  color: dashboardMode === 'soldier' ? '#000000' : '#FFFFFF',
                  border: dashboardMode === 'soldier' ? '1px solid #FFFFFF' : '1px solid #FFFFFF',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.2s ease',
                  boxShadow: dashboardMode === 'soldier' ? '0 0 10px rgba(255, 255, 255, 0.5), inset 0 0 10px rgba(255, 255, 255, 0.2)' : '0 0 5px rgba(255, 255, 255, 0.3)',
                  textShadow: dashboardMode === 'soldier' ? 'none' : '0 0 5px rgba(255, 255, 255, 0.5)'
                }}
              >
                <RobotOutlined style={{ fontSize: '10px' }} />
                TACTICAL
              </button>
              <button
                onClick={() => onModeSwitch('coc')}
                disabled={isTransitioning}
                className="glow-button"
                style={{
                  padding: '2px 12px',
                  fontSize: '11px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  backgroundColor: dashboardMode === 'coc' ? '#FFFFFF' : '#1A1A1A',
                  color: dashboardMode === 'coc' ? '#000000' : '#FFFFFF',
                  border: dashboardMode === 'coc' ? '1px solid #FFFFFF' : '1px solid #FFFFFF',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.2s ease',
                  boxShadow: dashboardMode === 'coc' ? '0 0 10px rgba(255, 255, 255, 0.5), inset 0 0 10px rgba(255, 255, 255, 0.2)' : '0 0 5px rgba(255, 255, 255, 0.3)',
                  textShadow: dashboardMode === 'coc' ? 'none' : '0 0 5px rgba(255, 255, 255, 0.5)'
                }}
              >
                <AimOutlined style={{ fontSize: '10px' }} />
                COMMAND
              </button>
            </div>
          </div>
        </div>

        <div style={{
          display: 'flex',
          gap: '24px',
          alignItems: 'center'
        }}>
          <div style={{
            display: 'flex',
            gap: '20px',
            alignItems: 'center'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 8px',
              backgroundColor: '#1A1A1A',
              borderRadius: '4px',
              border: '1px solid #333333',
              boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.2)'
            }}>
              <DatabaseOutlined style={{ fontSize: '10px', color: '#1565C0' }} />
              <span style={{
                fontSize: '10px',
                fontWeight: '600',
                color: '#1565C0',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {(eaData || []).length} EAS
              </span>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 8px',
              backgroundColor: connected ? '#0D2818' : '#2D1B1B',
              borderRadius: '4px',
              border: `1px solid ${connected ? '#2E7D32' : '#D32F2F'}`,
              boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.2)'
            }}>
              <div style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: connected ? '#4CAF50' : '#F44336',
                boxShadow: connected ? '0 0 4px rgba(76, 175, 80, 0.6)' : '0 0 4px rgba(244, 67, 54, 0.6)'
              }}></div>
              <span style={{
                fontSize: '10px',
                fontWeight: '600',
                color: connected ? '#4CAF50' : '#F44336',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {connected ? 'LIVE' : 'DOWN'}
              </span>
            </div>

            {/* WebSocket Status Indicator */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 8px',
              backgroundColor: dataSource === 'mt5_websocket' ? '#0D2818' : '#2D1B1B',
              borderRadius: '4px',
              border: `1px solid ${dataSource === 'mt5_websocket' ? '#2E7D32' : '#D32F2F'}`,
              boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.2)'
            }}>
              <div style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: dataSource === 'mt5_websocket' ? '#4CAF50' : '#FF6600',
                boxShadow: dataSource === 'mt5_websocket' ? '0 0 4px rgba(76, 175, 80, 0.6)' : '0 0 4px rgba(255, 102, 0, 0.6)'
              }}></div>
              <span style={{
                fontSize: '10px',
                fontWeight: '600',
                color: dataSource === 'mt5_websocket' ? '#4CAF50' : '#FF6600',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {dataSource === 'mt5_websocket' ? 'MT5' : dataSource === 'loading' ? 'CONN' : 'DEMO'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TickerBar;