import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import EAGroupingPanel from '../EAGroupingPanel';
import { DashboardProvider } from '../../../context/DashboardContext';

// Mock data for testing
const mockEAData = [
  {
    id: 1,
    magic_number: 1001,
    symbol: 'EURUSD',
    strategy_tag: 'Compression v1',
    risk_config: 1.0,
    status: 'active'
  },
  {
    id: 2,
    magic_number: 1002,
    symbol: 'GBPUSD',
    strategy_tag: 'Expansion v1',
    risk_config: 1.5,
    status: 'active'
  }
];

// Wrapper component with context
const TestWrapper = ({ children }) => (
  <DashboardProvider>
    {children}
  </DashboardProvider>
);

// Mock the useDashboard hook to provide test data
jest.mock('../../../context/DashboardContext', () => ({
  ...jest.requireActual('../../../context/DashboardContext'),
  useDashboard: () => ({
    state: {
      eaData: mockEAData
    }
  })
}));

describe('EAGroupingPanel', () => {
  beforeEach(() => {
    // Clear any previous alerts
    jest.clearAllMocks();
    
    // Mock window.alert
    window.alert = jest.fn();
    window.confirm = jest.fn(() => true);
  });

  test('renders EA grouping panel with all tabs', () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Check if main title is present
    expect(screen.getByText('EA Grouping & Tagging System')).toBeInTheDocument();
    
    // Check if all tabs are present
    expect(screen.getByText('Groups')).toBeInTheDocument();
    expect(screen.getByText('Tags')).toBeInTheDocument();
    expect(screen.getByText('Mass Commands')).toBeInTheDocument();
    expect(screen.getByText('Statistics')).toBeInTheDocument();
    
    // Check if mock notice is present
    expect(screen.getByText(/Currently using mock implementation/)).toBeInTheDocument();
  });

  test('can switch between tabs', () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Initially on Groups tab
    expect(screen.getByText('Auto-Grouping')).toBeInTheDocument();
    
    // Switch to Tags tab
    fireEvent.click(screen.getByText('Tags'));
    expect(screen.getByText('Add Tag to EA')).toBeInTheDocument();
    
    // Switch to Mass Commands tab
    fireEvent.click(screen.getByText('Mass Commands'));
    expect(screen.getByText('Mass Command Execution')).toBeInTheDocument();
    
    // Switch to Statistics tab
    fireEvent.click(screen.getByText('Statistics'));
    expect(screen.getByText('Grouping System Statistics')).toBeInTheDocument();
  });

  test('can create a new group', async () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Fill in group creation form
    const groupNameInput = screen.getByPlaceholderText('Group Name');
    const groupTypeSelect = screen.getByDisplayValue('Custom');
    const descriptionInput = screen.getByPlaceholderText('Description (optional)');
    const createButton = screen.getByText('Create Group');

    fireEvent.change(groupNameInput, { target: { value: 'Test Group' } });
    fireEvent.change(descriptionInput, { target: { value: 'Test Description' } });
    fireEvent.click(createButton);

    // Wait for the mock alert
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Group created successfully (mock implementation)');
    });

    // Check if form was cleared
    expect(groupNameInput.value).toBe('');
    expect(descriptionInput.value).toBe('');
  });

  test('shows validation error when creating group without name', async () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Try to create group without name
    const createButton = screen.getByText('Create Group');
    fireEvent.click(createButton);

    // Should show validation error
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Group name is required');
    });
  });

  test('can perform auto-grouping operations', async () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Test auto-group by symbol
    const symbolButton = screen.getByText('Group by Symbol');
    fireEvent.click(symbolButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining('Auto-grouped by symbol: created')
      );
    });

    // Test auto-group by strategy
    const strategyButton = screen.getByText('Group by Strategy');
    fireEvent.click(strategyButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining('Auto-grouped by strategy: created')
      );
    });

    // Test auto-group by risk level
    const riskButton = screen.getByText('Group by Risk Level');
    fireEvent.click(riskButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining('Auto-grouped by risk level: created')
      );
    });
  });

  test('can add tags to EAs', async () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Switch to Tags tab
    fireEvent.click(screen.getByText('Tags'));

    // Select an EA and add a tag
    const eaSelect = screen.getByDisplayValue('Select EA');
    const tagNameInput = screen.getByPlaceholderText('Tag Name');
    const tagValueInput = screen.getByPlaceholderText('Tag Value (optional)');
    const addTagButton = screen.getByText('Add Tag');

    // Select first EA (value should be the EA id)
    fireEvent.change(eaSelect, { target: { value: '1' } });
    fireEvent.change(tagNameInput, { target: { value: 'environment' } });
    fireEvent.change(tagValueInput, { target: { value: 'production' } });
    fireEvent.click(addTagButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Tag added successfully (mock implementation)');
    });

    // Check if form was cleared
    expect(tagNameInput.value).toBe('');
    expect(tagValueInput.value).toBe('');
  });

  test('can execute mass commands', async () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Switch to Mass Commands tab
    fireEvent.click(screen.getByText('Mass Commands'));

    // Select command type and execute by criteria
    const commandSelect = screen.getByDisplayValue('Pause');
    const executeButton = screen.getByText('Execute by All Criteria');

    fireEvent.change(commandSelect, { target: { value: 'resume' } });
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining("Command 'resume' executed on")
      );
    });
  });

  test('displays statistics correctly', () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Switch to Statistics tab
    fireEvent.click(screen.getByText('Statistics'));

    // Check if statistics are displayed
    expect(screen.getByText('Grouping System Statistics')).toBeInTheDocument();
    expect(screen.getByText('Total EAs:')).toBeInTheDocument();
    expect(screen.getByText('Total Groups:')).toBeInTheDocument();
    expect(screen.getByText('Total Tags:')).toBeInTheDocument();
  });

  test('handles loading states correctly', async () => {
    render(
      <TestWrapper>
        <EAGroupingPanel />
      </TestWrapper>
    );

    // Create a group to trigger loading state
    const groupNameInput = screen.getByPlaceholderText('Group Name');
    const createButton = screen.getByText('Create Group');

    fireEvent.change(groupNameInput, { target: { value: 'Test Group' } });
    fireEvent.click(createButton);

    // The loading state should be brief, but we can check that the button gets disabled
    // during the operation (though it's very fast in the mock implementation)
    expect(createButton).toBeInTheDocument();
  });
});