// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Simple and reliable matchMedia mock
window.matchMedia = window.matchMedia || function(query) {
  return {
    matches: false,
    media: query,
    onchange: null,
    addListener: function() {},
    removeListener: function() {},
    addEventListener: function() {},
    removeEventListener: function() {},
    dispatchEvent: function() {},
  };
};

// Mock getComputedStyle
window.getComputedStyle = window.getComputedStyle || function() {
  return {
    getPropertyValue: function() { return ''; }
  };
};

// Mock ResizeObserver
global.ResizeObserver = global.ResizeObserver || class ResizeObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock IntersectionObserver
global.IntersectionObserver = global.IntersectionObserver || class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock electron API for tests
if (typeof window !== 'undefined') {
  window.electronAPI = window.electronAPI || {
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
}