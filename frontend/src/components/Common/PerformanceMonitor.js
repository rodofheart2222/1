import React, { useState, useEffect } from 'react';
import { Card, Progress, Row, Col, Statistic, Tag } from 'antd';
import { 
  ThunderboltOutlined, 
  ClockCircleOutlined, 
  DatabaseOutlined,
  WifiOutlined
} from '@ant-design/icons';

const PerformanceMonitor = ({ visible = false }) => {
  const [metrics, setMetrics] = useState({
    fps: 0,
    memoryUsage: 0,
    loadTime: 0,
    connectionLatency: 0,
    renderTime: 0
  });

  useEffect(() => {
    if (!visible) return;

    let frameCount = 0;
    let lastTime = performance.now();
    let animationId;

    const measurePerformance = () => {
      const currentTime = performance.now();
      frameCount++;

      if (currentTime - lastTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
        
        // Memory usage (if available)
        const memoryUsage = performance.memory 
          ? Math.round((performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100)
          : 0;

        // Connection latency simulation (replace with actual WebSocket ping)
        const connectionLatency = Math.random() * 50 + 10;

        // Render time from navigation timing
        const renderTime = performance.timing 
          ? performance.timing.loadEventEnd - performance.timing.navigationStart
          : 0;

        setMetrics({
          fps,
          memoryUsage,
          loadTime: renderTime,
          connectionLatency: Math.round(connectionLatency),
          renderTime: Math.round(performance.now() - currentTime)
        });

        frameCount = 0;
        lastTime = currentTime;
      }

      animationId = requestAnimationFrame(measurePerformance);
    };

    measurePerformance();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [visible]);

  if (!visible) return null;

  const getPerformanceColor = (value, thresholds) => {
    if (value >= thresholds.good) return '#52c41a';
    if (value >= thresholds.warning) return '#faad14';
    return '#ff4d4f';
  };

  const fpsColor = getPerformanceColor(metrics.fps, { good: 50, warning: 30 });
  const memoryColor = getPerformanceColor(100 - metrics.memoryUsage, { good: 70, warning: 50 });
  const latencyColor = getPerformanceColor(100 - metrics.connectionLatency, { good: 80, warning: 60 });

  return (
    <div 
      className="performance-monitor glass-card"
      style={{
        position: 'fixed',
        top: '120px',
        right: '24px',
        width: '300px',
        zIndex: 999,
        padding: '16px',
        fontSize: '12px'
      }}
    >
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        marginBottom: '16px',
        color: '#00d4ff',
        fontWeight: 'bold'
      }}>
        <ThunderboltOutlined style={{ marginRight: '8px' }} />
        Performance Monitor
      </div>

      <Row gutter={[8, 8]}>
        <Col span={12}>
          <div className="metric-item">
            <div style={{ color: '#a6a6a6', fontSize: '10px', marginBottom: '4px' }}>
              FPS
            </div>
            <div style={{ color: fpsColor, fontSize: '16px', fontWeight: 'bold' }}>
              {metrics.fps}
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div className="metric-item">
            <div style={{ color: '#a6a6a6', fontSize: '10px', marginBottom: '4px' }}>
              Latency
            </div>
            <div style={{ color: latencyColor, fontSize: '16px', fontWeight: 'bold' }}>
              {metrics.connectionLatency}ms
            </div>
          </div>
        </Col>
        <Col span={24}>
          <div style={{ marginBottom: '8px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '4px'
            }}>
              <span style={{ color: '#a6a6a6', fontSize: '10px' }}>Memory Usage</span>
              <span style={{ color: memoryColor, fontSize: '10px', fontWeight: 'bold' }}>
                {metrics.memoryUsage}%
              </span>
            </div>
            <Progress 
              percent={metrics.memoryUsage} 
              strokeColor={memoryColor}
              showInfo={false}
              size="small"
            />
          </div>
        </Col>
      </Row>

      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        marginTop: '12px',
        paddingTop: '8px',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <Tag 
          color={metrics.fps > 50 ? 'success' : metrics.fps > 30 ? 'warning' : 'error'}
          style={{ fontSize: '10px', margin: 0 }}
        >
          {metrics.fps > 50 ? 'Excellent' : metrics.fps > 30 ? 'Good' : 'Poor'}
        </Tag>
        <span style={{ color: '#666', fontSize: '10px' }}>
          Load: {metrics.loadTime}ms
        </span>
      </div>
    </div>
  );
};

export default PerformanceMonitor;