/**
 * COCDashboard component tests
 */
import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render, createMockEAData, createMockGlobalStats, createMockNewsEvents, setupCommonMocks } from '../../test-utils';
import COCDashboard from '../Dashboard/COCDashboard';

setupCommonMocks();

describe('COCDashboard Component', () => {
  const mockEAData = createMockEAData(10);
  const mockGlobalStats = createMockGlobalStats();
  const mockNewsEvents = createMockNewsEvents(5);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders COC dashboard with all main tabs', () => {
    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        globalStats: mockGlobalStats,
        newsEvents: mockNewsEvents
      }
    });

    // Check for main tabs
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
    expect(screen.getByText('Controls')).toBeInTheDocument();
    expect(screen.getByText('Risk Management')).toBeInTheDocument();
    expect(screen.getByText('Action Queue')).toBeInTheDocument();
  });

  test('switches between tabs correctly', async () => {
    render(<COCDashboard />, {
      initialState: { eaData: mockEAData, globalStats: mockGlobalStats }
    });

    // Initially should show Overview tab
    expect(screen.getByText('Global Statistics')).toBeInTheDocument();

    // Click Performance tab
    fireEvent.click(screen.getByText('Performance'));
    await waitFor(() => {
      expect(screen.getByText('Performance Breakdown')).toBeInTheDocument();
    });

    // Click Filters tab
    fireEvent.click(screen.getByText('Filters'));
    await waitFor(() => {
      expect(screen.getByText('Filter Panel')).toBeInTheDocument();
    });
  });

  test('displays global statistics in overview tab', () => {
    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        globalStats: mockGlobalStats
      }
    });

    // Check global stats display
    expect(screen.getByText(/2,450.75/)).toBeInTheDocument(); // Total profit
    expect(screen.getByText(/25/)).toBeInTheDocument(); // Total EAs
    expect(screen.getByText(/22/)).toBeInTheDocument(); // Active EAs
    expect(screen.getByText(/68.5%/)).toBeInTheDocument(); // Win rate
  });

  test('shows performance breakdown by symbol and strategy', async () => {
    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        globalStats: mockGlobalStats
      }
    });

    // Navigate to Performance tab
    fireEvent.click(screen.getByText('Performance'));

    await waitFor(() => {
      // Should show breakdown by symbol
      expect(screen.getByText('EURUSD')).toBeInTheDocument();
      expect(screen.getByText('GBPUSD')).toBeInTheDocument();
      
      // Should show breakdown by strategy
      expect(screen.getByText('Scalper_v1')).toBeInTheDocument();
      expect(screen.getByText('Swing_v2')).toBeInTheDocument();
    });
  });

  test('applies filters and shows filtered results', async () => {
    render(<COCDashboard />, {
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

    // Navigate to Filters tab
    fireEvent.click(screen.getByText('Filters'));

    await waitFor(() => {
      // Should show filter controls
      expect(screen.getByText('Symbol Filter')).toBeInTheDocument();
      expect(screen.getByText('Strategy Filter')).toBeInTheDocument();
      expect(screen.getByText('Status Filter')).toBeInTheDocument();
    });

    // Apply filter
    const symbolFilter = screen.getByDisplayValue('EURUSD');
    expect(symbolFilter).toBeInTheDocument();
  });

  test('shows global action controls', async () => {
    render(<COCDashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Navigate to Controls tab
    fireEvent.click(screen.getByText('Controls'));

    await waitFor(() => {
      // Should show global action buttons
      expect(screen.getByText('Pause All EAs')).toBeInTheDocument();
      expect(screen.getByText('Resume All EAs')).toBeInTheDocument();
      expect(screen.getByText('Emergency Stop')).toBeInTheDocument();
      expect(screen.getByText('Close All Positions')).toBeInTheDocument();
    });
  });

  test('handles batch EA operations', async () => {
    const mockServices = require('../../test-utils').mockServices;
    mockServices.api.sendBatchCommands.mockResolvedValue({
      status: 'success',
      commands: [{ ea_id: 1 }, { ea_id: 2 }]
    });

    render(<COCDashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Navigate to Controls tab
    fireEvent.click(screen.getByText('Controls'));

    await waitFor(() => {
      const pauseAllButton = screen.getByText('Pause All EAs');
      fireEvent.click(pauseAllButton);
    });

    // Should show confirmation dialog
    expect(screen.getByText(/Confirm Action/)).toBeInTheDocument();

    // Confirm action
    fireEvent.click(screen.getByText('Confirm'));

    await waitFor(() => {
      expect(mockServices.api.sendBatchCommands).toHaveBeenCalled();
    });
  });

  test('displays risk management interface', async () => {
    render(<COCDashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Navigate to Risk Management tab
    fireEvent.click(screen.getByText('Risk Management'));

    await waitFor(() => {
      expect(screen.getByText('Risk Adjustment')).toBeInTheDocument();
      expect(screen.getByText('Per EA')).toBeInTheDocument();
      expect(screen.getByText('Per Strategy')).toBeInTheDocument();
      expect(screen.getByText('Global')).toBeInTheDocument();
    });
  });

  test('shows action queue with pending commands', async () => {
    const mockCommands = [
      {
        id: 1,
        ea_id: 12345,
        command_type: 'pause',
        status: 'pending',
        execution_time: new Date(Date.now() + 300000).toISOString()
      },
      {
        id: 2,
        ea_id: 67890,
        command_type: 'resume',
        status: 'executed',
        execution_time: new Date(Date.now() - 60000).toISOString()
      }
    ];

    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        commands: mockCommands
      }
    });

    // Navigate to Action Queue tab
    fireEvent.click(screen.getByText('Action Queue'));

    await waitFor(() => {
      expect(screen.getByText('Command Queue')).toBeInTheDocument();
      expect(screen.getByText('pause')).toBeInTheDocument();
      expect(screen.getByText('resume')).toBeInTheDocument();
      expect(screen.getByText('pending')).toBeInTheDocument();
      expect(screen.getByText('executed')).toBeInTheDocument();
    });
  });

  test('handles real-time updates via WebSocket', async () => {
    const mockServices = require('../../test-utils').mockServices;
    let messageCallback;

    mockServices.webSocket.onMessage.mockImplementation(callback => {
      messageCallback = callback;
    });

    render(<COCDashboard />, {
      initialState: { eaData: mockEAData, globalStats: mockGlobalStats }
    });

    // Simulate WebSocket update
    const update = {
      type: 'global_stats_update',
      data: {
        totalProfit: 3000.00,
        totalEAs: 30
      }
    };

    if (messageCallback) {
      messageCallback(JSON.stringify(update));
    }

    await waitFor(() => {
      expect(screen.getByText(/3,000.00/)).toBeInTheDocument();
      expect(screen.getByText(/30/)).toBeInTheDocument();
    });
  });

  test('shows EA grouping and tagging interface', async () => {
    render(<COCDashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Should show EA grouping controls
    expect(screen.getByText('EA Groups')).toBeInTheDocument();
    
    // Click to expand grouping section
    fireEvent.click(screen.getByText('EA Groups'));

    await waitFor(() => {
      expect(screen.getByText('Create Group')).toBeInTheDocument();
      expect(screen.getByText('Manage Tags')).toBeInTheDocument();
    });
  });

  test('handles emergency stop functionality', async () => {
    const mockServices = require('../../test-utils').mockServices;
    mockServices.api.sendBatchCommands.mockResolvedValue({ status: 'success' });

    render(<COCDashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Navigate to Controls tab
    fireEvent.click(screen.getByText('Controls'));

    await waitFor(() => {
      const emergencyButton = screen.getByText('Emergency Stop');
      fireEvent.click(emergencyButton);
    });

    // Should show emergency confirmation
    expect(screen.getByText(/Emergency Stop/)).toBeInTheDocument();
    expect(screen.getByText(/This will immediately stop all EAs/)).toBeInTheDocument();

    // Confirm emergency stop
    fireEvent.click(screen.getByText('Execute Emergency Stop'));

    await waitFor(() => {
      expect(mockServices.api.sendBatchCommands).toHaveBeenCalledWith(
        expect.objectContaining({
          command_type: 'emergency_stop'
        })
      );
    });
  });

  test('shows filtered statistics in overview', async () => {
    const filteredEAData = mockEAData.filter(ea => ea.symbol === 'EURUSD');
    
    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        globalStats: mockGlobalStats,
        filters: {
          symbol: 'EURUSD',
          strategy: 'all',
          status: 'all',
          search: ''
        }
      }
    });

    // Should show filtered statistics
    const filteredStats = screen.getByText('Filtered View');
    expect(filteredStats).toBeInTheDocument();

    // Should show count of filtered EAs
    expect(screen.getByText(`${filteredEAData.length} EAs`)).toBeInTheDocument();
  });

  test('handles search functionality', async () => {
    render(<COCDashboard />, {
      initialState: { eaData: mockEAData }
    });

    // Navigate to Filters tab
    fireEvent.click(screen.getByText('Filters'));

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search EAs...');
      fireEvent.change(searchInput, { target: { value: 'Scalper' } });
    });

    // Should filter results based on search
    const scalperEAs = mockEAData.filter(ea => ea.strategy_tag.includes('Scalper'));
    await waitFor(() => {
      expect(screen.getByText(`${scalperEAs.length} results`)).toBeInTheDocument();
    });
  });

  test('displays system health indicators', () => {
    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        connected: true,
        connectionError: null
      }
    });

    // Should show system health status
    expect(screen.getByTestId('system-health')).toBeInTheDocument();
    expect(screen.getByText('System Healthy')).toBeInTheDocument();
  });

  test('handles disconnection gracefully', () => {
    render(<COCDashboard />, {
      initialState: {
        eaData: mockEAData,
        connected: false,
        connectionError: 'WebSocket disconnected'
      }
    });

    // Should show disconnection warning
    expect(screen.getByText(/System Disconnected/)).toBeInTheDocument();
    expect(screen.getByText(/Limited functionality/)).toBeInTheDocument();
  });

  test('persists tab selection', () => {
    const localStorageMock = {
      getItem: jest.fn(() => 'performance'),
      setItem: jest.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock
    });

    render(<COCDashboard />);

    // Should start with saved tab
    expect(screen.getByText('Performance Breakdown')).toBeInTheDocument();
  });

  test('shows keyboard shortcuts help', async () => {
    render(<COCDashboard />);

    // Press help key
    fireEvent.keyDown(document, { key: 'F1' });

    await waitFor(() => {
      expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
      expect(screen.getByText('Ctrl+P: Pause All')).toBeInTheDocument();
      expect(screen.getByText('Ctrl+R: Resume All')).toBeInTheDocument();
    });
  });
});

describe('COCDashboard Performance', () => {
  test('renders efficiently with large datasets', () => {
    const largeEAData = createMockEAData(100);
    
    const start = performance.now();
    render(<COCDashboard />, {
      initialState: { eaData: largeEAData }
    });
    const end = performance.now();

    expect(end - start).toBeLessThan(1000);
    expect(screen.getByTestId('coc-dashboard')).toBeInTheDocument();
  });

  test('handles tab switching efficiently', async () => {
    const tabs = ['Overview', 'Performance', 'Filters', 'Controls', 'Risk Management', 'Action Queue'];
    
    render(<COCDashboard />, {
      initialState: { eaData: createMockEAData(50) }
    });

    const start = performance.now();

    // Switch through all tabs
    for (const tab of tabs) {
      fireEvent.click(screen.getByText(tab));
      await waitFor(() => {
        expect(screen.getByText(tab)).toHaveClass('ant-tabs-tab-active');
      });
    }

    const end = performance.now();
    expect(end - start).toBeLessThan(2000);
  });
});

describe('COCDashboard Accessibility', () => {
  test('meets accessibility requirements', () => {
    render(<COCDashboard />);

    const dashboard = screen.getByTestId('coc-dashboard');
    
    // Check ARIA attributes
    expect(dashboard).toHaveAttribute('role', 'main');
    
    // Check tab navigation
    const tabs = screen.getAllByRole('tab');
    tabs.forEach(tab => {
      expect(tab).toHaveAttribute('tabIndex');
    });
  });

  test('supports keyboard navigation', () => {
    render(<COCDashboard />);

    // Test tab navigation with keyboard
    fireEvent.keyDown(screen.getByRole('tablist'), {
      key: 'ArrowRight',
      code: 'ArrowRight'
    });

    expect(screen.getByText('Performance')).toHaveFocus();
  });

  test('provides appropriate screen reader support', () => {
    render(<COCDashboard />, {
      initialState: { eaData: createMockEAData(5) }
    });

    // Check ARIA labels and descriptions
    expect(screen.getByLabelText('Commander-in-Chief Dashboard')).toBeInTheDocument();
    expect(screen.getByText(/5 Expert Advisors monitored/)).toBeInTheDocument();
  });
});


