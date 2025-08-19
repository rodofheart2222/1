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
import { quickAPITest } from '../../utils/connectionTest';
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api';

const { Text, Paragraph } = Typography;

const ConnectionTest = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [priceUpdates, setPriceUpdates] = useState({});
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    // Initial API connection test
    testAPIConnection();
  }, []);

  const addMessage = (text, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev.slice(-9), { text, type, timestamp }]);
  };

  const testAPIConnection = async () => {
    setConnectionStatus('connecting');
    addMessage('Testing backend API connection...', 'info');
    
    try {
      const result = await quickAPITest();
      if (result.success) {
        setConnectionStatus('connected');
        setTestResults(prev => ({ ...prev, connection: 'success' }));
        addMessage('✅ Backend API connected successfully', 'success');
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      setConnectionStatus('error');
      setTestResults(prev => ({ ...prev, connection: 'error' }));
      addMessage(`❌ API connection failed: ${error.message}`, 'error');
    }
  };

  const testConnection = async () => {
    setConnectionStatus('connecting');
    setMessages([]);
    setTestResults({});
    
    try {
      addMessage('Starting connection test...', 'info');
      
      // Test 1: Backend API Connection
      addMessage('Testing backend API...', 'info');
      const apiResult = await quickAPITest();
      if (apiResult.success) {
        setTestResults(prev => ({ ...prev, api: 'success' }));
        addMessage('✅ Backend API connected successfully', 'success');
      } else {
        throw new Error(apiResult.message);
      }
      
      // Test 2: EA List
      addMessage('Testing EA data retrieval...', 'info');
      const eaResponse = await fetch(`${API_BASE_URL}${API_ENDPOINTS.eaList}`);
      if (eaResponse.ok) {
        const eaData = await eaResponse.json();
        setTestResults(prev => ({ ...prev, eaData: 'success' }));
        addMessage(`✅ Found ${eaData.length} EAs in system`, 'success');
      } else {
        setTestResults(prev => ({ ...prev, eaData: 'warning' }));
        addMessage('⚠️ No EA data available', 'warning');
      }
      
      // Test 3: MT5 Integration
      addMessage('Testing MT5 integration...', 'info');
      const mt5Response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.mt5Status}`);
      if (mt5Response.ok) {
        const mt5Data = await mt5Response.json();
        setTestResults(prev => ({ ...prev, mt5: 'success' }));
        addMessage('✅ MT5 integration working', 'success');
      } else {
        setTestResults(prev => ({ ...prev, mt5: 'warning' }));
        addMessage('⚠️ MT5 integration not available', 'warning');
      }
      
      setConnectionStatus('connected');
      
    } catch (error) {
      setTestResults(prev => ({ ...prev, connection: 'error' }));
      addMessage(`❌ Connection test failed: ${error.message}`, 'error');
      setConnectionStatus('error');
    }
  };

  const refreshTest = () => {
    testAPIConnection();
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
      <Card title="Backend API Connection Test" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>API Status: </Text>
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
                Test API
              </Button>
              <Button 
                icon={<ReloadOutlined />}
                onClick={refreshTest}
                disabled={connectionStatus === 'connecting'}
              >
                Refresh
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
                {getTestResultIcon(testResults.api)}
                <Text style={{ marginLeft: '8px' }}>Backend API Connection</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                {getTestResultIcon(testResults.eaData)}
                <Text style={{ marginLeft: '8px' }}>EA Data Retrieval</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                {getTestResultIcon(testResults.mt5)}
                <Text style={{ marginLeft: '8px' }}>MT5 Integration</Text>
              </div>
            </div>
          </div>

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