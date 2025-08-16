/**
 * SoldierEAPanel component tests
 */
import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render, createMockEAData, setupCommonMocks } from '../../test-utils';
import SoldierEAPanel from '../Dashboard/SoldierEAPanel';

setupCommonMocks();

describe('SoldierEAPanel Component', () => {
  const mockEAData = createMockEAData(1)[0];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders EA information correctly', () => {
    render(<SoldierEAPanel ea={mockEAData} />);

    // Check EA basic info
    expect(screen.getByText(mockEAData.symbol)).toBeInTheDocument();
    expect(screen.getByText(mockEAData.strategy_tag)).toBeInTheDocument();
    expect(screen.getByText(`#${mockEAData.magic_number}`)).toBeInTheDocument();

    // Check profit display
    expect(screen.getByText(mockEAData.current_profit.toString())).toBeInTheDocument();

    // Check status indicator
    expect(screen.getByText(mockEAData.status)).toBeInTheDocument();
  });

  test('displays live trade information', () => {
    const eaWithTrades = {
      ...mockEAData,
      open_positions: 2,
      sl_value: 1.0850,
      tp_value: 1.0950,
      trailing_active: true,
    };

    render(<SoldierEAPanel ea={eaWithTrades} />);

    // Check positions
    expect(screen.getByText('2')).toBeInTheDocument(); // open positions

    // Check SL/TP values
    expect(screen.getByText(/1.0850/)).toBeInTheDocument();
    expect(screen.getByText(/1.0950/)).toBeInTheDocument();

    // Check trailing status
    expect(screen.getByText(/Trailing: Active/)).toBeInTheDocument();
  });

  test('shows module status grid', () => {
    const eaWithModules = {
      ...mockEAData,
      module_status: {
        BB: 'expansion',
        RSI: 'oversold',
        MA: 'bullish',
        Volume: 'high'
      }
    };

    render(<SoldierEAPanel ea={eaWithModules} />);

    // Check module indicators
    expect(screen.getByText('BB')).toBeInTheDocument();
    expect(screen.getByText('expansion')).toBeInTheDocument();
    expect(screen.getByText('RSI')).toBeInTheDocument();
    expect(screen.getByText('oversold')).toBeInTheDocument();
    expect(screen.getByText('MA')).toBeInTheDocument();
    expect(screen.getByText('bullish')).toBeInTheDocument();
  });

  test('displays performance metrics', () => {
    const eaWithPerformance = {
      ...mockEAData,
      performance_metrics: {
        profit_factor: 1.75,
        expected_payoff: 32.50,
        drawdown: 4.2,
        z_score: 2.3,
        trade_count: 89
      }
    };

    render(<SoldierEAPanel ea={eaWithPerformance} />);

    // Check performance values
    expect(screen.getByText('1.75')).toBeInTheDocument(); // profit factor
    expect(screen.getByText('32.50')).toBeInTheDocument(); // expected payoff
    expect(screen.getByText('4.2%')).toBeInTheDocument(); // drawdown
    expect(screen.getByText('2.3')).toBeInTheDocument(); // z-score
    expect(screen.getByText('89')).toBeInTheDocument(); // trade count
  });

  test('shows trade journal with last trades', () => {
    const eaWithTrades = {
      ...mockEAData,
      last_trades: [
        '[BUY] EURUSD 1.0 @ 1.0900 → 1.0925 (+25.0)',
        '[SELL] EURUSD 0.5 @ 1.0880 → 1.0860 (+10.0)',
        '[BUY] EURUSD 1.0 @ 1.0870 → 1.0895 (+25.0)'
      ]
    };

    render(<SoldierEAPanel ea={eaWithTrades} />);

    // Check trade entries
    expect(screen.getByText(/\[BUY\] EURUSD 1.0 @ 1.0900/)).toBeInTheDocument();
    expect(screen.getByText(/\[SELL\] EURUSD 0.5 @ 1.0880/)).toBeInTheDocument();
    expect(screen.getByText(/\+25.0/)).toBeInTheDocument();
  });

  test('indicates commander commands status', () => {
    const eaWithCommand = {
      ...mockEAData,
      coc_override: true,
      last_command: {
        command_type: 'pause',
        reason: 'news_event',
        timestamp: new Date().toISOString()
      }
    };

    render(<SoldierEAPanel ea={eaWithCommand} />);

    // Check command indicator
    expect(screen.getByText(/COC Override/)).toBeInTheDocument();
    expect(screen.getByText(/pause/)).toBeInTheDocument();
    expect(screen.getByText(/news_event/)).toBeInTheDocument();
  });

  test('handles different EA statuses with appropriate styling', () => {
    const activeEA = { ...mockEAData, status: 'active' };
    const pausedEA = { ...mockEAData, status: 'paused' };
    const errorEA = { ...mockEAData, status: 'error' };

    // Test active status
    const { rerender } = render(<SoldierEAPanel ea={activeEA} />);
    expect(screen.getByTestId('ea-panel')).toHaveClass('status-active');

    // Test paused status
    rerender(<SoldierEAPanel ea={pausedEA} />);
    expect(screen.getByTestId('ea-panel')).toHaveClass('status-paused');

    // Test error status
    rerender(<SoldierEAPanel ea={errorEA} />);
    expect(screen.getByTestId('ea-panel')).toHaveClass('status-error');
  });

  test('shows profit/loss with appropriate colors', () => {
    const profitableEA = { ...mockEAData, current_profit: 250.75 };
    const losingEA = { ...mockEAData, current_profit: -125.50 };

    // Test profitable EA
    const { rerender } = render(<SoldierEAPanel ea={profitableEA} />);
    expect(screen.getByText('250.75')).toHaveClass('profit-positive');

    // Test losing EA
    rerender(<SoldierEAPanel ea={losingEA} />);
    expect(screen.getByText('-125.50')).toHaveClass('profit-negative');
  });

  test('handles missing or incomplete data gracefully', () => {
    const incompleteEA = {
      id: 1,
      magic_number: 12345,
      symbol: 'EURUSD',
      strategy_tag: 'Test_Strategy',
      status: 'active',
      // Missing other fields
    };

    render(<SoldierEAPanel ea={incompleteEA} />);

    // Should still render basic information
    expect(screen.getByText('EURUSD')).toBeInTheDocument();
    expect(screen.getByText('Test_Strategy')).toBeInTheDocument();
    
    // Should handle missing data gracefully
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  test('updates in real-time when EA data changes', () => {
    const initialEA = { ...mockEAData, current_profit: 100.0 };
    
    const { rerender } = render(<SoldierEAPanel ea={initialEA} />);
    expect(screen.getByText('100')).toBeInTheDocument();

    // Update profit
    const updatedEA = { ...initialEA, current_profit: 150.75 };
    rerender(<SoldierEAPanel ea={updatedEA} />);
    expect(screen.getByText('150.75')).toBeInTheDocument();
  });

  test('handles click events for detailed view', () => {
    const onClickMock = jest.fn();
    
    render(<SoldierEAPanel ea={mockEAData} onClick={onClickMock} />);

    const panel = screen.getByTestId('ea-panel');
    fireEvent.click(panel);

    expect(onClickMock).toHaveBeenCalledWith(mockEAData);
  });

  test('shows connection status indicator', () => {
    const recentEA = {
      ...mockEAData,
      last_seen: new Date().toISOString() // Recent
    };

    const staleEA = {
      ...mockEAData,
      last_seen: new Date(Date.now() - 300000).toISOString() // 5 minutes ago
    };

    // Test recent connection
    const { rerender } = render(<SoldierEAPanel ea={recentEA} />);
    expect(screen.getByTestId('connection-indicator')).toHaveClass('connected');

    // Test stale connection
    rerender(<SoldierEAPanel ea={staleEA} />);
    expect(screen.getByTestId('connection-indicator')).toHaveClass('disconnected');
  });

  test('formats numbers and values correctly', () => {
    const eaWithPreciseValues = {
      ...mockEAData,
      current_profit: 1234.567890,
      sl_value: 1.234567,
      tp_value: 1.987654,
      performance_metrics: {
        profit_factor: 1.23456789,
        expected_payoff: 123.456789,
        drawdown: 12.3456789
      }
    };

    render(<SoldierEAPanel ea={eaWithPreciseValues} />);

    // Check number formatting (should be rounded appropriately)
    expect(screen.getByText('1,234.57')).toBeInTheDocument(); // profit
    expect(screen.getByText('1.23457')).toBeInTheDocument(); // SL (5 decimals)
    expect(screen.getByText('1.98765')).toBeInTheDocument(); // TP (5 decimals)
    expect(screen.getByText('1.23')).toBeInTheDocument(); // PF (2 decimals)
  });

  test('shows appropriate tooltips for complex data', async () => {
    const eaWithTooltips = {
      ...mockEAData,
      module_status: {
        BB: 'expansion',
        RSI: 'oversold'
      }
    };

    render(<SoldierEAPanel ea={eaWithTooltips} />);

    // Hover over module status
    const bbModule = screen.getByText('BB');
    fireEvent.mouseOver(bbModule);

    await waitFor(() => {
      expect(screen.getByText(/Bollinger Bands/)).toBeInTheDocument();
    });
  });

  test('handles accessibility requirements', () => {
    render(<SoldierEAPanel ea={mockEAData} />);

    const panel = screen.getByTestId('ea-panel');
    
    // Check ARIA attributes
    expect(panel).toHaveAttribute('role', 'article');
    expect(panel).toHaveAttribute('aria-label');
    expect(panel).toHaveAttribute('tabIndex', '0');
  });

  test('responsive layout adjustments', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 480,
    });

    render(<SoldierEAPanel ea={mockEAData} />);

    const panel = screen.getByTestId('ea-panel');
    expect(panel).toHaveClass('mobile-layout');
  });
});

describe('SoldierEAPanel Performance', () => {
  test('renders quickly with complex data', () => {
    const complexEA = {
      ...createMockEAData(1)[0],
      module_status: {
        BB: 'expansion',
        RSI: 'oversold',
        MA: 'bullish',
        MACD: 'signal',
        Stoch: 'overbought',
        Volume: 'high',
        ATR: 'volatile',
        Support: 'holding',
        Resistance: 'broken'
      },
      last_trades: Array.from({ length: 20 }, (_, i) => 
        `[${i % 2 === 0 ? 'BUY' : 'SELL'}] EURUSD 1.0 @ 1.${1000 + i} → 1.${1025 + i} (+${25 + i})`
      )
    };

    const start = performance.now();
    render(<SoldierEAPanel ea={complexEA} />);
    const end = performance.now();

    expect(end - start).toBeLessThan(100); // Should render within 100ms
    expect(screen.getByTestId('ea-panel')).toBeInTheDocument();
  });

  test('handles frequent updates efficiently', () => {
    let renderCount = 0;
    const TestWrapper = ({ ea }) => {
      renderCount++;
      return <SoldierEAPanel ea={ea} />;
    };

    const { rerender } = render(<TestWrapper ea={mockEAData} />);

    const start = performance.now();
    
    // Simulate frequent updates
    for (let i = 0; i < 20; i++) {
      const updatedEA = {
        ...mockEAData,
        current_profit: mockEAData.current_profit + i,
        last_seen: new Date().toISOString()
      };
      rerender(<TestWrapper ea={updatedEA} />);
    }

    const end = performance.now();
    
    expect(end - start).toBeLessThan(500); // Should handle updates quickly
    expect(renderCount).toBe(21); // Initial + 20 updates
  });
});


