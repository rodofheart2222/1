import React, { useState, useEffect } from 'react';
import SmoothTicker from '../Common/SmoothTicker';

const SmoothTickerTest = () => {
  const [testValue, setTestValue] = useState(1.0847);

  useEffect(() => {
    // Generate random price changes every 2 seconds
    const interval = setInterval(() => {
      const change = (Math.random() - 0.5) * 0.01; // Random change between -0.005 and +0.005
      setTestValue(prev => Math.max(0, prev + change));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleManualChange = () => {
    const change = (Math.random() - 0.5) * 0.02;
    setTestValue(prev => Math.max(0, prev + change));
  };

  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#111',
      color: '#fff',
      fontFamily: 'monospace'
    }}>
      <h3>Smooth Ticker Test</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '24px', marginBottom: '10px' }}>
          <SmoothTicker 
            targetValue={testValue}
            decimals={5}
            flowSpeed={1800}
            showChangeIndicator={true}
          />
        </div>
        
        <div style={{ fontSize: '14px', color: '#888' }}>
          Target: {testValue.toFixed(5)}
        </div>
      </div>

      <button 
        onClick={handleManualChange}
        style={{
          padding: '10px 20px',
          backgroundColor: '#333',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Manual Change
      </button>

      <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
        This component automatically changes the value every 2 seconds to test smooth ticking.
        The number should smoothly animate between values, not jump instantly.
      </div>
    </div>
  );
};

export default SmoothTickerTest;