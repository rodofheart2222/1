import React from 'react';
import { Badge, Tooltip } from 'antd';
import { WifiOutlined, DisconnectOutlined } from '@ant-design/icons';

const ConnectionStatus = ({ connected }) => {
  return (
    <div className={`connection-status ${connected ? 'connected' : 'disconnected'} glass-card`}>
      <Tooltip title={connected ? 'Connected to backend' : 'Disconnected from backend'}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {connected ? (
            <WifiOutlined style={{ color: '#52c41a', fontSize: '14px' }} />
          ) : (
            <DisconnectOutlined style={{ color: '#ff4d4f', fontSize: '14px' }} />
          )}
          <span style={{ 
            fontWeight: 600, 
            fontSize: '12px',
            color: connected ? '#52c41a' : '#ff4d4f'
          }}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
          <div 
            className={`status-indicator ${connected ? 'online' : 'offline'}`}
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: connected ? '#52c41a' : '#ff4d4f',
              boxShadow: connected 
                ? '0 0 8px rgba(82, 196, 26, 0.6)' 
                : '0 0 8px rgba(255, 77, 79, 0.6)',
              animation: connected ? 'pulse 2s infinite' : 'none'
            }}
          />
        </div>
      </Tooltip>
    </div>
  );
};

export default ConnectionStatus;