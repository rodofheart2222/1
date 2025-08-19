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
import '../../styles/liquid-glass-theme.css';

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
        <button
          className="liquid-glass-button liquid-glass-button-primary"
          onClick={() => setDrawerVisible(true)}
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 56,
            height: 56,
            zIndex: 1000,
            borderRadius: '50%',
            fontSize: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          <PlusOutlined />
        </button>
      </Tooltip>

      <Drawer
        title={
          <div style={{ color: 'var(--lg-content)', fontWeight: 'bold' }}>
            Quick Actions
          </div>
        }
        placement="right"
        width={300}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        className="liquid-glass-panel"
        bodyStyle={{
          padding: '16px',
          background: 'color-mix(in srgb, var(--lg-glass) 10%, transparent)',
          backdropFilter: 'blur(12px) saturate(var(--lg-saturation))',
          WebkitBackdropFilter: 'blur(12px) saturate(var(--lg-saturation))',
          color: 'var(--lg-content)',
          border: 'none'
        }}
        headerStyle={{
          background: 'color-mix(in srgb, var(--lg-glass) 15%, transparent)',
          backdropFilter: 'blur(12px) saturate(var(--lg-saturation))',
          WebkitBackdropFilter: 'blur(12px) saturate(var(--lg-saturation))',
          color: 'var(--lg-content)',
          borderBottom: '1px solid color-mix(in srgb, var(--lg-light) calc(var(--lg-glass-reflex-light) * 8%), transparent)'
        }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {actions.map(action => (
            <button
              key={action.key}
              className="liquid-glass-button liquid-glass-button-medium"
              onClick={() => {
                action.onClick?.();
                setDrawerVisible(false);
              }}
              style={{
                width: '100%',
                height: '48px',
                fontSize: '14px',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                gap: '12px',
                '--lg-action': action.color,
                border: 'none',
                cursor: 'pointer'
              }}
            >
              {action.icon}
              <span>{action.label}</span>
            </button>
          ))}
        </Space>
      </Drawer>
    </>
  );
};

export default FloatingActionButton;