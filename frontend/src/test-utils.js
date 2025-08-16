/**
 * Test utilities for React components
 */
import React from 'react';
import { render } from '@testing-library/react';
import { DashboardProvider } from './context/DashboardContext';

// Mock Ant Design components that might cause issues in tests
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  notification: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
  message: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock WebSocket
const mockWebSocket = {
  connect: jest.fn().mockResolvedValue(true),
  disconnect: jest.fn(),
  send: jest.fn(),
  onMessage: jest.fn(),
  removeListeners: jest.fn(),
};

jest.mock('./services/webSocketService', () => ({
  connect: mockWebSocket.connect,
  disconnect: mockWebSocket.disconnect,
  send: mockWebSocket.send,
  onMessage: mockWebSocket.onMessage,
  removeListeners: mockWebSocket.removeListeners,
}));

// Mock API service
const mockApiService = {
  getEAData: jest.fn(),
  getGlobalStats: jest.fn(),
  getNewsEvents: jest.fn(),
  sendEACommand: jest.fn(),
  sendBatchCommands: jest.fn(),
  uploadBacktestReport: jest.fn(),
  getBacktestComparison: jest.fn(),
};

jest.mock('./services/api', () => mockApiService);

// Mock Electron API
const mockElectronAPI = {
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
};

// Mock window.electronAPI
Object.defineProperty(window, 'electronAPI', {
  value: mockElectronAPI,
  writable: true,
});

// Custom render function with providers
export const renderWithProviders = (ui, options = {}) => {
  const { initialState = {}, ...renderOptions } = options;

  const defaultState = {
    connected: true,
    connecting: false,
    connectionError: null,
    eaData: [],
    globalStats: {
      totalProfit: 0,
      totalEAs: 0,
      activeEAs: 0,
      winRate: 0,
      drawdown: 0,
    },
    newsEvents: [],
    eaDataLoading: false,
    filters: {
      symbol: 'all',
      strategy: 'all',
      status: 'all',
      search: '',
    },
    commands: [],
    commandLoading: false,
    commandError: null,
    ...initialState,
  };

  function Wrapper({ children }) {
    return (
      <DashboardProvider initialState={defaultState}>
        {children}
      </DashboardProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock data generators
export const createMockEAData = (count = 5) => {
  const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF'];
  const strategies = ['Scalper_v1', 'Swing_v2', 'Breakout_v3', 'Mean_Reversion_v1'];
  
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    magic_number: 10000 + index,
    symbol: symbols[index % symbols.length],
    strategy_tag: strategies[index % strategies.length],
    status: index % 2 === 0 ? 'active' : 'paused',
    current_profit: 100 + (index * 50),
    open_positions: Math.floor(Math.random() * 3),
    sl_value: 1.0800 + (index * 0.001),
    tp_value: 1.0900 + (index * 0.001),
    trailing_active: index % 3 === 0,
    module_status: {
      BB: ['expansion', 'compression', 'neutral'][index % 3],
      RSI: ['overbought', 'oversold', 'neutral'][index % 3],
      MA: ['bullish', 'bearish', 'sideways'][index % 3],
    },
    performance_metrics: {
      profit_factor: 1.2 + (index * 0.1),
      expected_payoff: 20 + (index * 5),
      drawdown: 3 + (index * 0.5),
      z_score: 1.5 + (index * 0.2),
      trade_count: 30 + (index * 10),
    },
    last_trades: [
      `[BUY] ${symbols[index % symbols.length]} 1.0 @ 1.0900 → 1.0925 (+25.0)`,
      `[SELL] ${symbols[index % symbols.length]} 0.5 @ 1.0880 → 1.0860 (+10.0)`,
    ],
    last_seen: new Date().toISOString(),
    created_at: new Date().toISOString(),
  }));
};

export const createMockGlobalStats = () => ({
  totalProfit: 2450.75,
  dailyProfit: 150.25,
  weeklyProfit: 850.50,
  monthlyProfit: 2450.75,
  totalEAs: 25,
  activeEAs: 22,
  pausedEAs: 3,
  winRate: 68.5,
  avgWinRate: 65.2,
  totalDrawdown: 4.2,
  maxDrawdown: 6.8,
  totalTrades: 1245,
  profitableTrades: 853,
  performance: {
    bySymbol: [
      { symbol: 'EURUSD', profit: 850.25, eas: 8 },
      { symbol: 'GBPUSD', profit: 650.50, eas: 6 },
      { symbol: 'USDJPY', profit: 450.00, eas: 5 },
    ],
    byStrategy: [
      { strategy: 'Scalper_v1', profit: 950.75, eas: 10 },
      { strategy: 'Swing_v2', profit: 750.00, eas: 8 },
      { strategy: 'Breakout_v3', profit: 500.00, eas: 5 },
    ],
  },
});

export const createMockNewsEvents = (count = 5) => {
  const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD'];
  const impacts = ['high', 'medium', 'low'];
  const events = [
    'Non-Farm Payrolls',
    'Interest Rate Decision',
    'GDP Release',
    'Inflation Data',
    'Employment Report',
  ];

  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    currency: currencies[index % currencies.length],
    event_name: events[index % events.length],
    impact_level: impacts[index % impacts.length],
    event_time: new Date(Date.now() + (index * 3600000)).toISOString(), // Hours in future
    description: `Economic data release for ${currencies[index % currencies.length]}`,
    blackout_start: new Date(Date.now() + (index * 3600000) - 600000).toISOString(),
    blackout_end: new Date(Date.now() + (index * 3600000) + 600000).toISOString(),
    affected_symbols: [`${currencies[index % currencies.length]}USD`, `EUR${currencies[index % currencies.length]}`],
  }));
};

export const createMockBacktestData = () => ({
  benchmark: {
    profit_factor: 1.85,
    expected_payoff: 28.75,
    drawdown: 3.8,
    win_rate: 62.5,
    trade_count: 200,
    upload_date: new Date().toISOString(),
  },
  live_performance: {
    profit_factor: 1.65,
    expected_payoff: 25.50,
    drawdown: 5.2,
    win_rate: 58.0,
    trade_count: 149,
  },
  deviation_report: {
    overall_status: 'warning',
    alerts: [
      {
        metric: 'profit_factor',
        level: 'warning',
        deviation_percent: -10.8,
        message: 'Profit factor down 10.8% from backtest',
        visual_indicator: '🟡',
      },
      {
        metric: 'drawdown',
        level: 'warning',
        deviation_percent: 36.8,
        message: 'Drawdown increased 36.8% from backtest',
        visual_indicator: '🟡',
      },
    ],
    recommendations: [
      'Monitor performance closely',
      'Consider reducing position size',
      'Review strategy parameters',
    ],
    should_flag_for_demotion: false,
  },
});

// Mock services for tests
export const mockServices = {
  webSocket: mockWebSocket,
  api: mockApiService,
  electron: mockElectronAPI,
};

// Test helpers
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0));

export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
  window.IntersectionObserverEntry = jest.fn();
};

// Mock ResizeObserver
export const createMockResizeObserver = () => {
  window.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  }));
};

// Setup common mocks
export const setupCommonMocks = () => {
  createMockIntersectionObserver();
  createMockResizeObserver();
  
  // Mock scrollIntoView
  Element.prototype.scrollIntoView = jest.fn();
  
  // Mock matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

export * from '@testing-library/react';
export { renderWithProviders as render };


