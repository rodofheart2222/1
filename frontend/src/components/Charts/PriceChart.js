import React, { useEffect, useState, useRef } from 'react';
import { Spin } from 'antd';
import { LineChartOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import chartService from '../../services/chartService';

const PriceChart = ({ symbol = 'EURUSD', width = 300, height = 200, showControls = false }) => {
  const canvasRef = useRef(null);
  const [priceData, setPriceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [timeframe, setTimeframe] = useState('1H');
  const [dataSource, setDataSource] = useState('mock_data');

  // Mock price data generator - in production, this would come from your backend
  const generateMockPriceData = (symbol, points = 50) => {
    // Use centralized price from chartService to ensure consistency
    const basePrice = chartService.getCurrentPrice(symbol);

    const data = [];
    let price = basePrice;
    const now = new Date();

    for (let i = points - 1; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000); // 1 hour intervals
      
      // Add some realistic price movement
      const volatility = symbol === 'XAUUSD' ? 5 : 0.001;
      const change = (Math.random() - 0.5) * volatility;
      price += change;
      
      data.push({
        timestamp: timestamp.toISOString(),
        price: parseFloat(price.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
        volume: Math.random() * 1000000
      });
    }

    return data;
  };

  useEffect(() => {
    const fetchChartData = async () => {
      setLoading(true);
      
      try {
        const chartData = await chartService.getChartData(symbol, timeframe, 50);
        
        if (chartData && chartData.data) {
          // Convert backend data format to component format
          const formattedData = chartData.data.map(point => ({
            timestamp: point.timestamp,
            price: point.close,
            volume: point.volume
          }));
          
          setPriceData(formattedData);
          setCurrentPrice(chartData.current_price);
          setPriceChange(chartData.price_change);
          setDataSource(chartData.source || 'unknown');
        }
      } catch (error) {
        console.error('Failed to fetch chart data:', error);
        // Fallback to mock data
        const mockData = generateMockPriceData(symbol);
        setPriceData(mockData);
        
        if (mockData.length > 0) {
          const latest = mockData[mockData.length - 1];
          const previous = mockData[mockData.length - 2];
          setCurrentPrice(latest.price);
          setPriceChange(latest.price - previous.price);
          setDataSource('mock_data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [symbol, timeframe]);

  useEffect(() => {
    if (!priceData.length || loading) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    // Set canvas size accounting for device pixel ratio
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Chart styling
    const padding = 20;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    // Find price range
    const prices = priceData.map(d => d.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 0.001;

    // Draw grid
    ctx.strokeStyle = '#1A1A1A';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
      const y = padding + (chartHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i <= 4; i++) {
      const x = padding + (chartWidth / 4) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
      ctx.stroke();
    }

    // Draw glowing price line (thinner)
    const lineColor = priceChange >= 0 ? '#00C851' : '#FF4444';
    
    // Create the path first
    ctx.beginPath();
    priceData.forEach((point, index) => {
      const x = padding + (index / (priceData.length - 1)) * chartWidth;
      const y = padding + (1 - (point.price - minPrice) / priceRange) * chartHeight;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    // Draw outer glow (thinner layers)
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 4;
    ctx.globalAlpha = 0.1;
    ctx.shadowColor = lineColor;
    ctx.shadowBlur = 8;
    ctx.stroke();

    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.2;
    ctx.shadowBlur = 5;
    ctx.stroke();

    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.3;
    ctx.shadowBlur = 3;
    ctx.stroke();

    // Draw main line with bright glow (thinner)
    ctx.lineWidth = 1;
    ctx.globalAlpha = 1;
    ctx.shadowColor = lineColor;
    ctx.shadowBlur = 2;
    ctx.stroke();

    // Reset shadow for other elements
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;

    // Draw price labels
    ctx.fillStyle = '#666666';
    ctx.font = '10px Inter';
    ctx.textAlign = 'right';
    
    // Max price
    ctx.fillText(maxPrice.toFixed(symbol === 'XAUUSD' ? 2 : 5), width - padding - 5, padding + 12);
    
    // Min price
    ctx.fillText(minPrice.toFixed(symbol === 'XAUUSD' ? 2 : 5), width - padding - 5, height - padding - 5);

    // Current price dot with glow (smaller)
    if (priceData.length > 0) {
      const lastPoint = priceData[priceData.length - 1];
      const x = padding + chartWidth;
      const y = padding + (1 - (lastPoint.price - minPrice) / priceRange) * chartHeight;
      
      const dotColor = priceChange >= 0 ? '#00C851' : '#FF4444';
      
      // Draw glowing dot (smaller)
      ctx.fillStyle = dotColor;
      ctx.shadowColor = dotColor;
      ctx.shadowBlur = 4;
      ctx.globalAlpha = 0.8;
      
      // Outer glow (smaller)
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, 2 * Math.PI);
      ctx.fill();
      
      // Inner bright dot (smaller)
      ctx.shadowBlur = 2;
      ctx.globalAlpha = 1;
      ctx.beginPath();
      ctx.arc(x, y, 1.5, 0, 2 * Math.PI);
      ctx.fill();
      
      // Reset shadow
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
    }

  }, [priceData, loading, width, height, symbol, priceChange]);

  if (loading) {
    return (
      <div style={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0F0F0F',
        borderRadius: '8px',
        border: '1px solid #1A1A1A'
      }}>
        <Spin size="small" />
      </div>
    );
  }

  return (
    <div style={{
      width,
      height,
      backgroundColor: '#0F0F0F',
      borderRadius: '8px',
      border: '1px solid #1A1A1A',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        position: 'absolute',
        top: '8px',
        left: '12px',
        right: '12px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        zIndex: 2
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
            fontWeight: '600',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {symbol}
          </span>
        </div>
        
        {showControls && (
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            style={{
              backgroundColor: '#1A1A1A',
              border: '1px solid #333333',
              color: '#CCCCCC',
              fontSize: '10px',
              padding: '2px 6px',
              borderRadius: '4px'
            }}
          >
            <option value="1M">1M</option>
            <option value="5M">5M</option>
            <option value="15M">15M</option>
            <option value="1H">1H</option>
            <option value="4H">4H</option>
            <option value="1D">1D</option>
          </select>
        )}
      </div>

      {/* Price Info */}
      <div style={{
        position: 'absolute',
        bottom: '8px',
        left: '12px',
        right: '12px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        zIndex: 2
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '2px'
        }}>
          <span style={{
            color: '#CCCCCC',
            fontSize: '13px',
            fontWeight: '700',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {currentPrice?.toFixed(symbol === 'XAUUSD' ? 2 : 5)}
          </span>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            {priceChange >= 0 ? (
              <ArrowUpOutlined style={{ color: '#00C851', fontSize: '10px' }} />
            ) : (
              <ArrowDownOutlined style={{ color: '#FF4444', fontSize: '10px' }} />
            )}
            <span style={{
              color: priceChange >= 0 ? '#00C851' : '#FF4444',
              fontSize: '10px',
              fontWeight: '600',
              fontFamily: '"JetBrains Mono", monospace'
            }}>
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(symbol === 'XAUUSD' ? 2 : 5)}
            </span>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          gap: '2px'
        }}>
          <div style={{
            fontSize: '9px',
            color: '#666666',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {timeframe}
          </div>
          <div style={{
            fontSize: '8px',
            color: dataSource === 'yahoo_finance' ? '#00C851' : '#666666',
            fontFamily: '"JetBrains Mono", monospace',
            textTransform: 'uppercase'
          }}>
            {dataSource === 'yahoo_finance' ? 'LIVE' : 'MOCK'}
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%'
        }}
      />
    </div>
  );
};

export default PriceChart;