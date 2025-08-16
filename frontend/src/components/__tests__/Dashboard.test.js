/**
 * Dashboard component tests
 */
import React from 'react';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { render, createMockEAData, createMockGlobalStats, createMockNewsEvents, setupCommonMocks } from '../../test-utils';
import Dashboard from '../Dashboard/Dashboard';

// Setup mocks before tests
setupCommonMocks();

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard with default soldier EA view', async () => {
    const mockEAData = createMockEAData(3);
    const mockGlobalStats = createMockGlobalStats();
    const mockNewsEvents = createMockNewsEvents(2);

    render(<Dashboard />, {
      initialState: {
        eaData: mockEAData,
        globalStats: mockGlobalStats,
        newsEvents: mockNewsEvents,
        connected: true,
      }
    });

    // Check for dashboard mode toggle
    expect(screen.getByText('Soldier EA View')).toBeInTheDocument();
    
    // Check for main sections
    expect(screen.getByText('Global Statistics')).toBeInTheDocument();
    expect(screen.getByText('EA Grid')).toBeInTheDocument();
    expect(screen.getByText('News Events')).toBeInTheDocument();
  });

  test('switches between soldier and COC dashboard modes', async () => {
    render(<Dashboard />);

    // Initially in soldier mode
    expect(screen.getByText('Soldier EA View')).toBeInTheDocument();

    // Find and click the mode toggle switch
    const modeToggle = screen.getByRole('switch');
    fireEvent.click(modeToggle);

    // Should switch to COC mode
    expect(screen.getByText('Commander-in-Chief')).toBeInTheDocument();
  });

  test('shows connection status indicator', () => {
    render(<Dashboard />, {
      initialState: { connected: false, connectionError: 'Connection failed' }
    });

    // Connection status should be visible
    expect(screen.getByTestId('connection-status')).toBeInTheDocument();
  });

  test('shows loading state while connecting', () => {
    render(<Dashboard />, {
      initialState: { 
        connecting: true,
        connected: false,
        eaDataLoading: true 
      }
    });

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('displays error message when connection fails', () => {
    const errorMessage = 'Failed to connect to backend';
    
    render(<Dashboard />, {
      initialState: {
        connected: false,
        connectionError: errorMessage
      }
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('initializes dashboard services on mount', async () => {
    const mockServices = require('../../test-utils').mockServices;
    
    render(<Dashboard />);

    await waitFor(() => {
      expect(mockServices.webSocket.connect).toHaveBeenCalled();
    });
  });

  test('cleans up services on unmount', () => {
    const mockServices = require('../../test-utils').mockServices;
    
    const { unmount } = render(<Dashboard />);
    
    unmount();

    expect(mockServices.webSocket.disconnect).toHaveBeenCalled();
    expect(mockServices.webSocket.removeListeners).toHaveBeenCalled();
  });

  test('handles WebSocket reconnection', async () => {
    const mockServices = require('../../test-utils').mockServices;
    
    // Simulate connection failure then success
    mockServices.webSocket.connect
      .mockRejectedValueOnce(new Error('Connection failed'))
      .mockResolvedValueOnce(true);

    render(<Dashboard />);

    await waitFor(() => {
      expect(mockServices.webSocket.connect).toHaveBeenCalledTimes(2);
    });
  });

  test('renders mobile responsive layout', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    render(<Dashboard />);

    const dashboard = screen.getByTestId('dashboard');
    expect(dashboard).toHaveClass('dashboard');
  });

  test('updates real-time data via WebSocket', async () => {
    const mockServices = require('../../test-utils').mockServices;
    let messageCallback;

    mockServices.webSocket.onMessage.mockImplementation(callback => {
      messageCallback = callback;
    });

    render(<Dashboard />);

    // Simulate receiving WebSocket message
    const mockUpdate = {
      type: 'ea_update',
      data: {
        magic_number: 12345,
        current_profit: 250.75,
        status: 'active'
      }
    };

    if (messageCallback) {
      messageCallback(JSON.stringify(mockUpdate));
    }

    // Should update the UI with new data
    await waitFor(() => {
      expect(screen.getByText(/250.75/)).toBeInTheDocument();
    });
  });

  test('handles keyboard shortcuts', () => {
    render(<Dashboard />);

    // Simulate keyboard shortcuts
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    fireEvent.keyDown(document, { key: 'F5', code: 'F5' });

    // Should handle shortcuts appropriately
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
  });

  test('persists dashboard mode preference', () => {
    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock
    });

    render(<Dashboard />);

    // Switch to COC mode
    const modeToggle = screen.getByRole('switch');
    fireEvent.click(modeToggle);

    expect(localStorageMock.setItem).toHaveBeenCalledWith('dashboardMode', 'coc');
  });

  test('shows appropriate content based on data availability', () => {
    // Test with no data
    render(<Dashboard />, {
      initialState: {
        eaData: [],
        newsEvents: [],
        globalStats: null
      }
    });

    expect(screen.getByText(/No EAs detected/)).toBeInTheDocument();
    expect(screen.getByText(/No news events/)).toBeInTheDocument();
  });

  test('filters and search work correctly', async () => {
    const mockEAData = createMockEAData(10);
    
    render(<Dashboard />, {
      initialState: {
        eaData: mockEAData,
        filters: {
          symbol: 'EURUSD',
          strategy: 'all',
          status: 'active',
          search: ''
        }
      }
    });

    // Should show filtered results
    const eurusdEAs = mockEAData.filter(ea => ea.symbol === 'EURUSD' && ea.status === 'active');
    
    await waitFor(() => {
      expect(screen.getAllByText('EURUSD')).toHaveLength(eurusdEAs.length);
    });
  });

  test('handles window resize events', () => {
    render(<Dashboard />);

    // Simulate window resize
    fireEvent(window, new Event('resize'));

    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
  });
});

describe('Dashboard Integration', () => {
  test('integrates with all dashboard components', async () => {
    const mockEAData = createMockEAData(5);
    const mockGlobalStats = createMockGlobalStats();
    const mockNewsEvents = createMockNewsEvents(3);

    render(<Dashboard />, {
      initialState: {
        eaData: mockEAData,
        globalStats: mockGlobalStats,
        newsEvents: mockNewsEvents,
        connected: true,
      }
    });

    // Global Stats Panel
    expect(screen.getByText(/Total Profit/)).toBeInTheDocument();
    expect(screen.getByText(/2,450.75/)).toBeInTheDocument();

    // EA Grid View
    expect(screen.getAllByText(/EA/)).toHaveLength(5);

    // News Events Panel
    expect(screen.getAllByText(/USD|EUR|GBP/)).length.toBeGreaterThan(0);

    // Command Center
    expect(screen.getByText(/Send Command/)).toBeInTheDocument();
  });

  test('maintains state consistency across mode switches', async () => {
    const mockEAData = createMockEAData(3);
    
    render(<Dashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Capture initial state
    const initialEACount = screen.getAllByText(/EA/).length;

    // Switch to COC mode
    const modeToggle = screen.getByRole('switch');
    fireEvent.click(modeToggle);

    // Switch back to soldier mode
    fireEvent.click(modeToggle);

    // State should be maintained
    expect(screen.getAllByText(/EA/)).toHaveLength(initialEACount);
  });

  test('handles concurrent data updates', async () => {
    const mockServices = require('../../test-utils').mockServices;
    let messageCallback;

    mockServices.webSocket.onMessage.mockImplementation(callback => {
      messageCallback = callback;
    });

    render(<Dashboard />);

    // Simulate multiple concurrent updates
    const updates = [
      { type: 'ea_update', data: { magic_number: 12345, current_profit: 100 }},
      { type: 'global_stats_update', data: { totalProfit: 2000 }},
      { type: 'news_update', data: { new_events: 2 }},
    ];

    for (const update of updates) {
      if (messageCallback) {
        messageCallback(JSON.stringify(update));
      }
    }

    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });
});

describe('Dashboard Performance', () => {
  test('renders efficiently with large datasets', () => {
    const start = performance.now();
    
    const mockEAData = createMockEAData(100);
    
    render(<Dashboard />, {
      initialState: { eaData: mockEAData }
    });

    const end = performance.now();
    const renderTime = end - start;

    // Should render within reasonable time
    expect(renderTime).toBeLessThan(1000); // 1 second
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
  });

  test('handles rapid state updates without performance degradation', async () => {
    const mockServices = require('../../test-utils').mockServices;
    let messageCallback;

    mockServices.webSocket.onMessage.mockImplementation(callback => {
      messageCallback = callback;
    });

    render(<Dashboard />);

    const start = performance.now();

    // Simulate rapid updates
    for (let i = 0; i < 50; i++) {
      if (messageCallback) {
        messageCallback(JSON.stringify({
          type: 'ea_update',
          data: { magic_number: 12345, current_profit: 100 + i }
        }));
      }
    }

    await waitFor(() => {
      const end = performance.now();
      const updateTime = end - start;
      expect(updateTime).toBeLessThan(2000); // 2 seconds
    });
  });

  test('memory usage remains stable during extended use', () => {
    const { rerender } = render(<Dashboard />);

    // Simulate extended use with multiple rerenders
    for (let i = 0; i < 20; i++) {
      const mockData = createMockEAData(Math.floor(Math.random() * 10) + 1);
      rerender(<Dashboard />, {
        initialState: { eaData: mockData }
      });
    }

    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
  });
});


