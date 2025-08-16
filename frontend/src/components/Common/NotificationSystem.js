import React, { createContext, useContext, useState, useCallback } from 'react';
import { notification } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  InfoCircleOutlined, 
  CloseCircleOutlined 
} from '@ant-design/icons';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [api, contextHolder] = notification.useNotification();

  const showNotification = useCallback((type, title, message, options = {}) => {
    const config = {
      message: title,
      description: message,
      placement: 'topRight',
      duration: options.duration || 4.5,
      className: `modern-notification ${type}`,
      style: {
        background: 'rgba(20, 20, 20, 0.95)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '12px',
        color: '#ffffff',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.8)'
      },
      ...options
    };

    switch (type) {
      case 'success':
        config.icon = <CheckCircleOutlined style={{ color: '#52c41a' }} />;
        config.style.borderLeft = '4px solid #52c41a';
        break;
      case 'error':
        config.icon = <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
        config.style.borderLeft = '4px solid #ff4d4f';
        break;
      case 'warning':
        config.icon = <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
        config.style.borderLeft = '4px solid #faad14';
        break;
      case 'info':
      default:
        config.icon = <InfoCircleOutlined style={{ color: '#00d4ff' }} />;
        config.style.borderLeft = '4px solid #00d4ff';
        break;
    }

    api[type](config);
  }, [api]);

  const success = useCallback((title, message, options) => {
    showNotification('success', title, message, options);
  }, [showNotification]);

  const error = useCallback((title, message, options) => {
    showNotification('error', title, message, options);
  }, [showNotification]);

  const warning = useCallback((title, message, options) => {
    showNotification('warning', title, message, options);
  }, [showNotification]);

  const info = useCallback((title, message, options) => {
    showNotification('info', title, message, options);
  }, [showNotification]);

  const value = {
    success,
    error,
    warning,
    info,
    showNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {contextHolder}
      {children}
    </NotificationContext.Provider>
  );
};