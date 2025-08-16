import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { message } from 'antd';
import NewsEventPanel from '../NewsEventPanel';

// Mock antd message
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  message: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock fetch
global.fetch = jest.fn();

const mockEvents = [
  {
    id: 1,
    event_time: new Date().toISOString(),
    currency: 'USD',
    impact_level: 'high',
    description: 'Non-Farm Payrolls',
    pre_minutes: 60,
    post_minutes: 60,
    is_active: false
  },
  {
    id: 2,
    event_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
    currency: 'EUR',
    impact_level: 'medium',
    description: 'ECB Interest Rate Decision',
    pre_minutes: 30,
    post_minutes: 30,
    is_active: false
  },
  {
    id: 3,
    event_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago (active)
    currency: 'GBP',
    impact_level: 'low',
    description: 'Manufacturing PMI',
    pre_minutes: 15,
    post_minutes: 45, // Still active
    is_active: true
  }
];

const mockBlackoutStatus = {
  EURUSD: {
    trading_allowed: true,
    active_restrictions: [],
    highest_impact_level: null
  },
  GBPUSD: {
    trading_allowed: false,
    active_restrictions: [mockEvents[2]],
    highest_impact_level: 'low'
  }
};

const mockImpactConfig = {
  high: { pre: 60, post: 60 },
  medium: { pre: 30, post: 30 },
  low: { pre: 15, post: 15 }
};

describe('NewsEventPanel', () => {
  beforeEach(() => {
    fetch.mockClear();
    message.success.mockClear();
    message.error.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders news events panel with today tab', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    expect(screen.getByText('News Events')).toBeInTheDocument();
    expect(screen.getByText('Today (3)')).toBeInTheDocument();
    expect(screen.getByText('Non-Farm Payrolls')).toBeInTheDocument();
    expect(screen.getByText('ECB Interest Rate Decision')).toBeInTheDocument();
    expect(screen.getByText('Manufacturing PMI')).toBeInTheDocument();
  });

  it('displays impact level tags correctly', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
    expect(screen.getByText('LOW')).toBeInTheDocument();
  });

  it('shows active blackout indicator for active events', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    expect(screen.getByText('Trading Restricted - Active Blackout')).toBeInTheDocument();
  });

  it('filters events by impact level', async () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    // Find and click the impact filter select
    const impactFilter = screen.getByDisplayValue('high,medium,low');
    fireEvent.mouseDown(impactFilter);
    
    // Deselect 'low' impact
    const lowOption = screen.getByText('Low');
    fireEvent.click(lowOption);
    
    // Click outside to close dropdown
    fireEvent.click(document.body);
    
    // Manufacturing PMI (low impact) should not be visible
    await waitFor(() => {
      expect(screen.queryByText('Manufacturing PMI')).not.toBeInTheDocument();
    });
    
    // High and medium impact events should still be visible
    expect(screen.getByText('Non-Farm Payrolls')).toBeInTheDocument();
    expect(screen.getByText('ECB Interest Rate Decision')).toBeInTheDocument();
  });

  it('switches between tabs correctly', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    // Click on Upcoming tab
    fireEvent.click(screen.getByText('Upcoming'));
    
    // Should show upcoming events content
    expect(screen.getByText('Upcoming')).toBeInTheDocument();
    
    // Click on Blackout Status tab
    fireEvent.click(screen.getByText('Blackout Status'));
    
    // Should show blackout status content
    expect(screen.getByText('Trading Blackout Status')).toBeInTheDocument();
  });

  it('opens configuration modal when settings button is clicked', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    const settingsButton = screen.getByRole('button', { name: /setting/i });
    fireEvent.click(settingsButton);
    
    expect(screen.getByText('Impact Level Configuration')).toBeInTheDocument();
    expect(screen.getByText('High Impact Events')).toBeInTheDocument();
    expect(screen.getByText('Medium Impact Events')).toBeInTheDocument();
    expect(screen.getByText('Low Impact Events')).toBeInTheDocument();
  });

  it('opens manual override modal when button is clicked', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    const overrideButton = screen.getByText('Manual Override');
    fireEvent.click(overrideButton);
    
    expect(screen.getByText('Manual Override')).toBeInTheDocument();
    expect(screen.getByText('This will temporarily allow trading for the selected symbol, ignoring news restrictions.')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    const mockOnRefresh = jest.fn();
    render(<NewsEventPanel events={mockEvents} onRefresh={mockOnRefresh} />);
    
    const refreshButton = screen.getAllByRole('button', { name: /reload/i })[0];
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/news/sync', { method: 'POST' });
      expect(message.success).toHaveBeenCalledWith('News events refreshed successfully');
      expect(mockOnRefresh).toHaveBeenCalled();
    });
  });

  it('handles configuration save', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true })
    });

    render(<NewsEventPanel events={mockEvents} />);
    
    // Open config modal
    const settingsButton = screen.getByRole('button', { name: /setting/i });
    fireEvent.click(settingsButton);
    
    // Find and click OK button
    const okButton = screen.getByRole('button', { name: 'OK' });
    fireEvent.click(okButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/news/config/impact-levels', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }));
    });
  });

  it('handles manual override submission', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    render(<NewsEventPanel events={mockEvents} />);
    
    // Open override modal
    const overrideButton = screen.getByText('Manual Override');
    fireEvent.click(overrideButton);
    
    // Fill form
    const symbolSelect = screen.getByPlaceholderText('Select symbol');
    fireEvent.mouseDown(symbolSelect);
    fireEvent.click(screen.getByText('EURUSD'));
    
    const reasonInput = screen.getByPlaceholderText('Reason for manual override...');
    fireEvent.change(reasonInput, { target: { value: 'Test override' } });
    
    // Submit form
    const okButton = screen.getByRole('button', { name: 'OK' });
    fireEvent.click(okButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/news/override/enable', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('EURUSD')
      }));
    });
  });

  it('displays empty state when no events', () => {
    render(<NewsEventPanel events={[]} />);
    
    expect(screen.getByText('No news events today')).toBeInTheDocument();
  });

  it('formats event times correctly', () => {
    const testEvent = {
      ...mockEvents[0],
      event_time: '2024-01-15T14:30:00Z'
    };
    
    render(<NewsEventPanel events={[testEvent]} />);
    
    // Should display time in HH:MM format
    expect(screen.getByText(/14:30/)).toBeInTheDocument();
  });

  it('shows blackout period information', () => {
    render(<NewsEventPanel events={mockEvents} />);
    
    expect(screen.getByText('Blackout: 60m before / 60m after')).toBeInTheDocument();
    expect(screen.getByText('Blackout: 30m before / 30m after')).toBeInTheDocument();
    expect(screen.getByText('Blackout: 15m before / 45m after')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('API Error'));

    render(<NewsEventPanel events={mockEvents} />);
    
    const refreshButton = screen.getAllByRole('button', { name: /reload/i })[0];
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('Failed to refresh news events');
    });
  });

  it('loads initial data on mount', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, impact_level_config: mockImpactConfig })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, blackout_status: mockBlackoutStatus })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, events: [] })
      });

    render(<NewsEventPanel events={mockEvents} />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/news/config/impact-levels');
      expect(fetch).toHaveBeenCalledWith('/api/news/blackout/status?symbols=EURUSD,GBPUSD,USDJPY,XAUUSD');
      expect(fetch).toHaveBeenCalledWith('/api/news/events/upcoming?hours=24');
    });
  });

  it('calculates time until event correctly', () => {
    const futureEvent = {
      ...mockEvents[0],
      event_time: new Date(Date.now() + 90 * 60 * 1000).toISOString() // 90 minutes from now
    };
    
    render(<NewsEventPanel events={[futureEvent]} />);
    
    // Switch to upcoming tab to see time calculation
    fireEvent.click(screen.getByText('Upcoming'));
    
    // Should show "1h 30m" format
    expect(screen.getByText(/1h 30m/)).toBeInTheDocument();
  });
});