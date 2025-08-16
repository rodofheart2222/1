import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock electron API
global.window.electronAPI = {
  connectWebSocket: jest.fn().mockResolvedValue({ success: true }),
  disconnectWebSocket: jest.fn().mockResolvedValue({ success: true }),
  sendWebSocketMessage: jest.fn().mockResolvedValue({ success: true }),
  onWebSocketMessage: jest.fn(),
  removeWebSocketListeners: jest.fn(),
  minimize: jest.fn(),
  maximize: jest.fn(),
  close: jest.fn(),
  getVersion: jest.fn().mockResolvedValue('1.0.0'),
  showNotification: jest.fn(),
  openDevTools: jest.fn()
};

describe('Electron App Integration', () => {
  test('renders main dashboard components', () => {
    render(<App />);
    
    // Check if main title is rendered
    expect(screen.getByText('MT5 Commander-in-Chief Dashboard')).toBeInTheDocument();
    
    // Check if footer is rendered
    expect(screen.getByText(/MT5 COC Dashboard ©2024/)).toBeInTheDocument();
  });

  test('dashboard context provider is working', () => {
    render(<App />);
    
    // The app should render without context errors
    expect(screen.getByText('MT5 Commander-in-Chief Dashboard')).toBeInTheDocument();
  });

  test('responsive layout is applied', () => {
    render(<App />);
    
    const layout = document.querySelector('.app-layout');
    expect(layout).toBeInTheDocument();
    expect(layout).toHaveClass('app-layout');
  });
});