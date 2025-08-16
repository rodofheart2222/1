import React, { useState } from 'react';
import { Button, Tooltip, Drawer, Space } from 'antd';
import { 
  PlusOutlined, 
  SettingOutlined, 
  ReloadOutlined, 
  FullscreenOutlined,
  BugOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';

const FloatingActionButton = ({ onRefresh, onSettings, onFullscreen, onDebug, onHelp }) => {
  const [drawerVisible, setDrawerVisible] = useState(false);

  const actions = [
    {
      key: 'refresh',
      icon: <ReloadOutlined />,
      label: 'Refresh Data',
      onClick: onRefresh,
      color: '#52c41a'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: onSettings,
      color: '#1890ff'
    },
    {
      key: 'fullscreen',
      icon: <FullscreenOutlined />,
      label: 'Fullscreen',
      onClick: onFullscreen,
      color: '#722ed1'
    },
    {
      key: 'debug',
      icon: <BugOutlined />,
      label: 'Debug Info',
      onClick: onDebug,
      color: '#fa8c16'
    },
    {
      key: 'help',
      icon: <QuestionCircleOutlined />,
      label: 'Help',
      onClick: onHelp,
      color: '#13c2c2'
    }
  ];

  return (
    <>
      <Tooltip title="Quick Actions" placement="left">
        <Button
          type="primary"
          shape="circle"
          size="large"
          icon={<PlusOutlined />}
          className="floating-action-btn glass-button"
          onClick={() => setDrawerVisible(true)}
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 56,
            height: 56,
            zIndex: 1000,
            background: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
            border: 'none',
            boxShadow: '0 8px 24px rgba(0, 212, 255, 0.4)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
        />
      </Tooltip>

      <Drawer
        title={
          <div style={{ color: '#ffffff', fontWeight: 'bold' }}>
            Quick Actions
          </div>
        }
        placement="right"
        width={300}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        className="glass-drawer"
        style={{
          background: 'rgba(20, 20, 20, 0.95)',
          backdropFilter: 'blur(20px)'
        }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {actions.map(action => (
            <Button
              key={action.key}
              type="default"
              size="large"
              icon={action.icon}
              className="glass-button"
              onClick={() => {
                action.onClick?.();
                setDrawerVisible(false);
              }}
              style={{
                width: '100%',
                height: '48px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                gap: '12px',
                background: `rgba(${action.color === '#52c41a' ? '82, 196, 26' : 
                  action.color === '#1890ff' ? '24, 144, 255' :
                  action.color === '#722ed1' ? '114, 46, 209' :
                  action.color === '#fa8c16' ? '250, 140, 22' :
                  '19, 194, 194'}, 0.1)`,
                border: `1px solid ${action.color}40`,
                color: '#ffffff'
              }}
            >
              <span style={{ fontSize: '14px', fontWeight: '500' }}>
                {action.label}
              </span>
            </Button>
          ))}
        </Space>
      </Drawer>
    </>
  );
};

export default FloatingActionButton;