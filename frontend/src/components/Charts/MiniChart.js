import React, { useEffect, useRef, useState } from 'react';
import './MiniChart.css';

const MiniChart = ({ 
  data = [], 
  width = 120, 
  height = 40, 
  color = '#00C851',
  strokeWidth = 1.5,
  responsive = false 
}) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width, height });

  // Handle responsive sizing
  useEffect(() => {
    if (!responsive) {
      setDimensions({ width, height });
      return;
    }

    const updateDimensions = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        const containerHeight = containerRef.current.offsetHeight;
        
        setDimensions({
          width: containerWidth || width,
          height: containerHeight || height
        });
      }
    };

    updateDimensions();
    
    // Use ResizeObserver if available, otherwise fall back to window resize
    if (typeof ResizeObserver !== 'undefined') {
      const resizeObserver = new ResizeObserver(updateDimensions);
      if (containerRef.current) {
        resizeObserver.observe(containerRef.current);
      }

      return () => {
        resizeObserver.disconnect();
      };
    } else {
      // Fallback for older browsers
      window.addEventListener('resize', updateDimensions);
      return () => {
        window.removeEventListener('resize', updateDimensions);
      };
    }
  }, [responsive, width, height]);

  useEffect(() => {
    if (!data || data.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      const dpr = window.devicePixelRatio || 1;
      
      const { width: canvasWidth, height: canvasHeight } = dimensions;
      
      // Ensure minimum dimensions
      if (canvasWidth < 10 || canvasHeight < 10) return;
    
      // Set canvas size accounting for device pixel ratio
      canvas.width = canvasWidth * dpr;
      canvas.height = canvasHeight * dpr;
      canvas.style.width = canvasWidth + 'px';
      canvas.style.height = canvasHeight + 'px';
      ctx.scale(dpr, dpr);

      // Clear canvas with smooth fade
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);

      // Extract and validate prices with better handling
      const prices = [];
      
      for (let i = 0; i < data.length; i++) {
        const d = data[i];
        let price = null;
        
        try {
          // Handle different data formats:
          // 1. Direct number: d = 1.2345
          // 2. Object with price: { price: 1.2345, timestamp: "..." }
          // 3. Object with close: { open: 1.2340, high: 1.2350, low: 1.2330, close: 1.2345 }
          if (typeof d === 'number') {
            price = d;
          } else if (d && typeof d === 'object') {
            price = d.price || d.close || d.value;
          }
          
          // Validate the price
          if (typeof price === 'number' && !isNaN(price) && isFinite(price)) {
            prices.push(price);
          }
        } catch (error) {
          console.warn('MiniChart: Error processing data point:', d, error);
        }
      }
      
      if (prices.length === 0) {
        console.warn('MiniChart: No valid prices found in data:', data);
        return;
      }
      
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      
      // Debug logging for development
      if (process.env.NODE_ENV === 'development' && prices.length > 0) {
        console.log('MiniChart prices:', {
          count: prices.length,
          min: minPrice,
          max: maxPrice,
          first: prices[0],
          last: prices[prices.length - 1]
        });
      }
      
      // Calculate price range with better fallback handling
      let priceRange = maxPrice - minPrice;
      if (priceRange === 0 || !isFinite(priceRange)) {
        // If all prices are the same, create a small range for visualization
        const avgPrice = (minPrice + maxPrice) / 2;
        priceRange = Math.abs(avgPrice * 0.001) || 0.001;
      }

      // Add padding to prevent clipping
      const padding = Math.max(strokeWidth + 1, 2);
      const chartWidth = Math.max(canvasWidth - (padding * 2), 1);
      const chartHeight = Math.max(canvasHeight - (padding * 2), 1);

      // Enable smooth rendering
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      
      // Create the path first
      ctx.beginPath();
      let hasValidPath = false;
      prices.forEach((price, index) => {
        const x = padding + (index / Math.max(prices.length - 1, 1)) * chartWidth;
        const y = padding + chartHeight - ((price - minPrice) / priceRange) * chartHeight;
        
        // Ensure coordinates are valid
        if (isFinite(x) && isFinite(y)) {
          if (index === 0 || !hasValidPath) {
            ctx.moveTo(x, y);
            hasValidPath = true;
          } else {
            ctx.lineTo(x, y);
          }
        }
      });

      if (hasValidPath) {
        // Draw glowing line effect (thinner)
        ctx.strokeStyle = color;
        
        // Outer glow layers (thinner)
        ctx.lineWidth = Math.max(strokeWidth * 2.5, 3);
        ctx.globalAlpha = 0.1;
        ctx.shadowColor = color;
        ctx.shadowBlur = 5;
        ctx.stroke();

        ctx.lineWidth = Math.max(strokeWidth * 2, 2.5);
        ctx.globalAlpha = 0.2;
        ctx.shadowBlur = 3;
        ctx.stroke();

        ctx.lineWidth = Math.max(strokeWidth * 1.5, 2);
        ctx.globalAlpha = 0.3;
        ctx.shadowBlur = 2;
        ctx.stroke();

        // Main line with bright glow (thinner)
        ctx.lineWidth = Math.max(strokeWidth * 0.8, 1);
        ctx.globalAlpha = 1;
        ctx.shadowColor = color;
        ctx.shadowBlur = 1;
        ctx.stroke();

        // Reset shadow and alpha
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
      }

    } catch (error) {
      console.error('MiniChart: Error rendering chart:', error);
    }
  }, [data, dimensions, color, strokeWidth]);

  const containerStyle = {
    width: responsive ? '100%' : `${width}px`,
    height: responsive ? '100%' : `${height}px`,
    minWidth: responsive ? '60px' : undefined,
    minHeight: responsive ? '20px' : undefined,
  };

  const containerClass = `mini-chart-container ${responsive ? 'mini-chart-responsive' : ''}`;

  // Show error state if no valid data
  if (!data || data.length === 0) {
    return (
      <div 
        ref={containerRef} 
        className="mini-chart-error" 
        style={containerStyle}
      >
        No Data
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className={containerClass}
      style={containerStyle}
    >
      <canvas ref={canvasRef} />
    </div>
  );
};

export default MiniChart;