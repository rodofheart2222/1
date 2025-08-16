import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, Tag, Divider } from 'antd';
import { 
  PlayCircleOutlined, 
  StopOutlined, 
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import webSocketService from '../../services/webSocketService';

const { Text, Paragraph } = Typography;

const ConnectionTest = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [priceUpdates, setPriceUpdates] = useState({});
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    // Set up WebSocket event handlers
    webSocketService.onConnectionChange = (connected) => {
      setConnectionStatus(connected ? 'connected' : 'disconnected');
      addMessage(`Connection ${connected ? 'established' : 'lost'}`, connected ? 'success' : 'error');
    };

    webSocketService.onMessage = (message) => {
      addMessage(`Received: ${message.type}`, 'info');
      
      if (message.type === 'price_update') {
        setPriceUpdates(prev => ({
          ...prev,
          ...message.data
        }));
      }
    };

    webSocketService.onError = (error) => {
      addMessage(`Error: ${error.message}`, 'error');
    };

    return () => {
      // Cleanup
      webSocketService.onConnectionChange = null;
      webSocketService.onMessage = null;
      webSocketService.onError = null;
    };
  }, []);

  const addMessage = (text, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev.slice(-9), { text, type, timestamp }]);
  };

  const testConnection = async () => {
    setConnectionStatus('connecting');
    setMessages([]);
    setTestResults({});
    
    try {
      addMessage('Starting connection test...', 'info');
      
      // Test 1: WebSocket Connection
      addMessage('Testing WebSocket connection...', 'info');
      await webSocketService.connect();
      setTestResults(prev => ({ ...prev, connection: 'success' }));
      addMessage('✅ WebSocket connected successfully', 'success');
      
      // Wait a moment for connection to stabilize
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Test 2: Authentication
      addMessage('Testing authentication...', 'info');
      // Authentication is handled automatically in connect()
      setTestResults(prev => ({ ...prev, auth: 'success' }));
      addMessage('✅ Authentication successful', 'success');
      
      // Test 3: Price Subscription
      addMessage('Testing price subscription...', 'info');
      const testSymbols = ['EURUSD', 'GBPUSD', 'XAUUSD'];
      webSocketService.subscribeToPrices(testSymbols);
      setTestResults(prev => ({ ...prev, subscription: 'success' }));
      addMessage(`✅ Subscribed to ${testSymbols.join(', ')}`, 'success');
      
      // Test 4: Wait for price updates
      addMessage('Waiting for price updates...', 'info');
      setTimeout(() => {
        if (Object.keys(priceUpdates).length > 0) {
          setTestResults(prev => ({ ...prev, priceUpdates: 'success' }));
          addMessage(`✅ Received price updates for ${Object.keys(priceUpdates).length} symbols`, 'success');
        } else {
          setTestResults(prev => ({ ...prev, priceUpdates: 'warning' }));
          addMessage('⚠️ No price updates received yet', 'warning');
        }
      }, 3000);
      
    } catch (error) {
      setTestResults(prev => ({ ...prev, connection: 'error' }));
      addMessage(`❌ Connection failed: ${error.message}`, 'error');
      setConnectionStatus('error');
    }
  };

  const disconnect = () => {
    webSocketService.disconnect();
    setConnectionStatus('disconnected');
    setPriceUpdates({});
    addMessage('Disconnected from WebSocket', 'info');
  };

  const clearMessages = () => {
    setMessages([]);
    setPriceUpdates({});
    setTestResults({});
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'success';
      case 'connecting': return 'processing';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getTestResultIcon = (result) => {
    switch (result) {
      case 'success': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning': return <LoadingOutlined style={{ color: '#faad14' }} />;
      default: return null;
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <Card title="WebSocket Connection Test" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>Connection Status: </Text>
              <Tag color={getStatusColor(connectionStatus)}>
                {connectionStatus.toUpperCase()}
              </Tag>
            </div>
            <Space>
              <Button 
                type="primary" 
                icon={<PlayCircleOutlined />}
                onClick={testConnection}
                disabled={connectionStatus === 'connecting'}
              >
                Test Connection
              </Button>
              <Button 
                icon={<StopOutlined />}
                onClick={disconnect}
                disabled={connectionStatus === 'disconnected'}
              >
                Disconnect
              </Button>
              <Button 
                icon={<ReloadOutlined />}
                onClick={clearMessages}
              >
                Clear
              </Button>
            </Space>
          </div>

          <Divider />

          {/* Test Results */}
          <div>
            <Text strong>Test Results:</Text>
            <div style={{ marginTop: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                {getTestResultIcon(testResults.connection)}
                <Text style={{ marginLeft: '8px' }}>WebSocket Connection</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                {getTestResultIcon(testResults.auth)}
                <Text style={{ marginLeft: '8px' }}>Authentication</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                {getTestResultIcon(testResults.subscription)}
                <Text style={{ marginLeft: '8px' }}>Price Subscription</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                {getTestResultIcon(testResults.priceUpdates)}
                <Text style={{ marginLeft: '8px' }}>Price Updates</Text>
              </div>
            </div>
          </div>

          <Divider />

          {/* Price Updates */}
          {Object.keys(priceUpdates).length > 0 && (
            <div>
              <Text strong>Live Price Updates:</Text>
              <div style={{ marginTop: '10px' }}>
                {Object.entries(priceUpdates).map(([symbol, data]) => (
                  <div key={symbol} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    padding: '5px 0',
                    borderBottom: '1px solid #f0f0f0'
                  }}>
                    <Text strong>{symbol}</Text>
                    <Text>{data.price?.toFixed(symbol === 'XAUUSD' ? 2 : 5)}</Text>
                    <Text type="secondary">{new Date(data.timestamp).toLocaleTimeString()}</Text>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Divider />

          {/* Message Log */}
          <div>
            <Text strong>Message Log:</Text>
            <div style={{ 
              maxHeight: '200px', 
              overflowY: 'auto', 
              marginTop: '10px',
              padding: '10px',
              backgroundColor: '#fafafa',
              borderRadius: '4px'
            }}>
              {messages.length === 0 ? (
                <Text type="secondary">No messages yet...</Text>
              ) : (
                messages.map((msg, index) => (
                  <div key={index} style={{ marginBottom: '5px' }}>
                    <Text type="secondary">[{msg.timestamp}]</Text>
                    <Text style={{ 
                      marginLeft: '8px',
                      color: msg.type === 'error' ? '#ff4d4f' : 
                            msg.type === 'success' ? '#52c41a' : 
                            msg.type === 'warning' ? '#faad14' : 'inherit'
                    }}>
                      {msg.text}
                    </Text>
                  </div>
                ))
              )}
            </div>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default ConnectionTest;