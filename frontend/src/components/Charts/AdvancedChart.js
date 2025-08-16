import React, { useEffect, useRef, useState } from 'react';
import { Spin } from 'antd';
import { LineChartOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import chartService from '../../services/chartService';
import './AdvancedChart.css';

const AdvancedChart = ({ 
  symbol = 'EURUSD', 
  width = 400, 
  height = 250, 
  showControls = true,
  theme = 'dark'
}) => {
  const canvasRef = useRef(null);
  const [priceData, setPriceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [timeframe, setTimeframe] = useState('1H');
  const [dataSource, setDataSource] = useState('mock_data');

  useEffect(() => {
    const fetchChartData = async () => {
      setLoading(true);
      
      try {
        const chartData = await chartService.getChartData(symbol, timeframe, 60);
        
        if (chartData && chartData.data) {
          const formattedData = chartData.data.map(point => ({
            timestamp: point.timestamp,
            price: point.close,
            volume: point.volume,
            high: point.high,
            low: point.low
          }));
          
          setPriceData(formattedData);
          setCurrentPrice(chartData.currentPrice || chartData.current_price);
          setPriceChange(chartData.priceChange || chartData.price_change);
          setDataSource(chartData.source || 'unknown');
        }
      } catch (error) {
        console.error('Failed to fetch chart data:', error);
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
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(dpr, dpr);

    // Clear canvas with gradient background
    const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
    bgGradient.addColorStop(0, '#0A0A0A');
    bgGradient.addColorStop(1, '#1A1A1A');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, width, height);

    const padding = 30;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    // Find price range
    const prices = priceData.map(d => d.price);
    const highs = priceData.map(d => d.high || d.price);
    const lows = priceData.map(d => d.low || d.price);
    
    const minPrice = Math.min(...lows);
    const maxPrice = Math.max(...highs);
    const priceRange = maxPrice - minPrice || 0.001;

    // Draw enhanced grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines with labels
    for (let i = 0; i <= 6; i++) {
      const y = padding + (chartHeight / 6) * i;
      const price = maxPrice - (priceRange / 6) * i;
      
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
      
      // Price labels
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textAlign = 'right';
      ctx.fillText(price.toFixed(symbol === 'XAUUSD' ? 2 : 5), width - padding - 5, y + 3);
    }

    // Vertical grid lines with time labels
    for (let i = 0; i <= 5; i++) {
      const x = padding + (chartWidth / 5) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
      ctx.stroke();
      
      // Time labels
      if (i < priceData.length) {
        const dataIndex = Math.floor((priceData.length - 1) * (i / 5));
        const timestamp = new Date(priceData[dataIndex]?.timestamp);
        const timeStr = timestamp.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        });
        
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = '9px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText(timeStr, x, height - padding + 15);
      }
    }

    // Create gradient for area fill
    const lineColor = priceChange >= 0 ? '#00FF88' : '#FF4466';
    const areaGradient = ctx.createLinearGradient(0, padding, 0, height - padding);
    areaGradient.addColorStop(0, `${lineColor}40`);
    areaGradient.addColorStop(0.7, `${lineColor}20`);
    areaGradient.addColorStop(1, `${lineColor}05`);

    // Draw area fill first
    ctx.beginPath();
    priceData.forEach((point, index) => {
      const x = padding + (index / (priceData.length - 1)) * chartWidth;
      const y = padding + (1 - (point.price - minPrice) / priceRange) * chartHeight;
      
      if (index === 0) {
        ctx.moveTo(x, height - padding);
        ctx.lineTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    // Close the area
    const lastX = padding + chartWidth;
    ctx.lineTo(lastX, height - padding);
    ctx.closePath();
    ctx.fillStyle = areaGradient;
    ctx.fill();

    // Draw high/low range as subtle background
    ctx.strokeStyle = `${lineColor}15`;
    ctx.lineWidth = 8;
    ctx.beginPath();
    priceData.forEach((point, index) => {
      const x = padding + (index / (priceData.length - 1)) * chartWidth;
      const highY = padding + (1 - (point.high - minPrice) / priceRange) * chartHeight;
      const lowY = padding + (1 - (point.low - minPrice) / priceRange) * chartHeight;
      
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
    });
    ctx.stroke();

    // Draw main price line with advanced glow
    const mainPath = new Path2D();
    priceData.forEach((point, index) => {
      const x = padding + (index / (priceData.length - 1)) * chartWidth;
      const y = padding + (1 - (point.price - minPrice) / priceRange) * chartHeight;
      
      if (index === 0) {
        mainPath.moveTo(x, y);
      } else {
        mainPath.lineTo(x, y);
      }
    });

    // Multiple glow layers for depth
    const glowLayers = [
      { width: 6, alpha: 0.1, blur: 12 },
      { width: 4, alpha: 0.2, blur: 8 },
      { width: 3, alpha: 0.3, blur: 5 },
      { width: 2, alpha: 0.5, blur: 3 },
      { width: 1.5, alpha: 1, blur: 1 }
    ];

    glowLayers.forEach(layer => {
      ctx.strokeStyle = lineColor;
      ctx.lineWidth = layer.width;
      ctx.globalAlpha = layer.alpha;
      ctx.shadowColor = lineColor;
      ctx.shadowBlur = layer.blur;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.stroke(mainPath);
    });

    // Reset shadow and alpha
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 1;

    // Draw price points with animated glow
    priceData.forEach((point, index) => {
      if (index % 5 === 0) { // Show every 5th point to avoid clutter
        const x = padding + (index / (priceData.length - 1)) * chartWidth;
        const y = padding + (1 - (point.price - minPrice) / priceRange) * chartHeight;
        
        // Outer glow
        ctx.fillStyle = `${lineColor}40`;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
        
        // Inner dot
        ctx.fillStyle = lineColor;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, 2 * Math.PI);
        ctx.fill();
      }
    });

    // Current price indicator with pulsing effect
    if (priceData.length > 0) {
      const lastPoint = priceData[priceData.length - 1];
      const x = padding + chartWidth;
      const y = padding + (1 - (lastPoint.price - minPrice) / priceRange) * chartHeight;
      
      // Pulsing outer ring
      const time = Date.now() * 0.003;
      const pulseRadius = 8 + Math.sin(time) * 2;
      
      ctx.fillStyle = `${lineColor}30`;
      ctx.beginPath();
      ctx.arc(x, y, pulseRadius, 0, 2 * Math.PI);
      ctx.fill();
      
      // Main indicator
      ctx.fillStyle = lineColor;
      ctx.shadowColor = lineColor;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();
      
      // Price line to edge
      ctx.strokeStyle = `${lineColor}60`;
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(width - 5, y);
      ctx.stroke();
      ctx.setLineDash([]);
      
      // Current price label
      ctx.fillStyle = lineColor;
      ctx.fillRect(width - 80, y - 10, 75, 20);
      ctx.fillStyle = '#000000';
      ctx.font = 'bold 11px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(
        lastPoint.price.toFixed(symbol === 'XAUUSD' ? 2 : 5),
        width - 42.5,
        y + 3
      );
      
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
    }

    // Volume bars at bottom
    const volumeHeight = 30;
    const volumes = priceData.map(d => d.volume || 0);
    const maxVolume = Math.max(...volumes);
    
    if (maxVolume > 0) {
      volumes.forEach((volume, index) => {
        const x = padding + (index / (priceData.length - 1)) * chartWidth;
        const barHeight = (volume / maxVolume) * volumeHeight;
        const barY = height - padding - barHeight;
        
        const volumeColor = priceData[index].price > (priceData[index - 1]?.price || priceData[index].price) 
          ? '#00FF8840' : '#FF446640';
        
        ctx.fillStyle = volumeColor;
        ctx.fillRect(x - 1, barY, 2, barHeight);
      });
    }

  }, [priceData, loading, width, height, symbol, priceChange, timeframe]);

  if (loading) {
    return (
      <div className="advanced-chart-loading" style={{ width, height }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="advanced-chart-container" style={{ width, height }}>
      {/* Header */}
      <div style={{
        position: 'absolute',
        top: '12px',
        left: '16px',
        right: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        zIndex: 2
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <LineChartOutlined style={{ 
            color: '#00FF88', 
            fontSize: '16px',
            filter: 'drop-shadow(0 0 4px #00FF88)'
          }} />
          <span style={{
            color: '#FFFFFF',
            fontSize: '16px',
            fontWeight: '700',
            fontFamily: '"JetBrains Mono", monospace',
            textShadow: '0 0 8px rgba(255, 255, 255, 0.3)'
          }}>
            {symbol}
          </span>
        </div>
        
        {showControls && (
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#FFFFFF',
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: '6px',
              backdropFilter: 'blur(10px)'
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
        bottom: '12px',
        left: '16px',
        right: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        zIndex: 2
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}>
          <span style={{
            color: '#FFFFFF',
            fontSize: '20px',
            fontWeight: '700',
            fontFamily: '"JetBrains Mono", monospace',
            textShadow: '0 0 12px rgba(255, 255, 255, 0.4)'
          }}>
            {currentPrice?.toFixed(symbol === 'XAUUSD' ? 2 : 5)}
          </span>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 8px',
            background: priceChange >= 0 ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 68, 102, 0.2)',
            borderRadius: '6px',
            border: `1px solid ${priceChange >= 0 ? '#00FF88' : '#FF4466'}40`
          }}>
            {priceChange >= 0 ? (
              <ArrowUpOutlined style={{ color: '#00FF88', fontSize: '12px' }} />
            ) : (
              <ArrowDownOutlined style={{ color: '#FF4466', fontSize: '12px' }} />
            )}
            <span style={{
              color: priceChange >= 0 ? '#00FF88' : '#FF4466',
              fontSize: '12px',
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
          gap: '4px'
        }}>
          <div style={{
            fontSize: '11px',
            color: 'rgba(255, 255, 255, 0.6)',
            fontFamily: '"JetBrains Mono", monospace'
          }}>
            {timeframe} • {priceData.length} points
          </div>
          <div style={{
            fontSize: '10px',
            color: dataSource === 'yahoo_finance' ? '#00FF88' : 'rgba(255, 255, 255, 0.4)',
            fontFamily: '"JetBrains Mono", monospace',
            textTransform: 'uppercase',
            padding: '2px 6px',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '4px'
          }}>
            {dataSource === 'yahoo_finance' ? 'LIVE' : 'DEMO'}
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

export default AdvancedChart;