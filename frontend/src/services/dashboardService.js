/**
 * Dashboard Service
 * Integrates API calls with Dashboard Context
 * Provides data fetching and real-time updates
 */

import apiService from './api';

class DashboardService {
  constructor() {
    this.isPolling = false;
    this.pollingInterval = null;
    this.updateCallbacks = new Set();
  }

  /**
   * Initialize dashboard service with context actions
   */
  initialize(actions) {
    this.actions = actions;
    return this;
  }

  /**
   * Start data polling
   */
  startPolling(intervalMs = 5000) {
    if (this.isPolling) {
      this.stopPolling();
    }

    this.isPolling = true;
    this.pollingInterval = setInterval(() => {
      this.fetchAllData();
    }, intervalMs);

    // Initial fetch
    this.fetchAllData();
  }

  /**
   * Stop data polling
   */
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    this.isPolling = false;
  }

  /**
   * Fetch all dashboard data
   */
  async fetchAllData() {
    try {
      await Promise.allSettled([
        this.fetchEAData(),
        this.fetchNewsEvents(),
        this.fetchGlobalStats()
      ]);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      if (this.actions) {
        this.actions.setConnectionError('Failed to fetch data from backend');
      }
    }
  }

  /**
   * Fetch EA status data
   */
  async fetchEAData() {
    try {
      console.log('📊 Fetching EA data...');
      if (this.actions) {
        this.actions.setEADataLoading(true);
      }

      const response = await apiService.getAllEAStatus();
      const eaData = response.eas || [];
      
      console.log(`✅ EA data fetched successfully: ${eaData.length} EAs found`);
      console.log('EA data:', eaData);

      if (this.actions) {
        this.actions.setEAData(eaData);
        this.actions.setEADataError(null);
      }

      return eaData;
    } catch (error) {
      console.error('❌ Error fetching EA data:', error);
      if (this.actions) {
        this.actions.setEADataError(error.message);
      }
      throw error;
    } finally {
      if (this.actions) {
        this.actions.setEADataLoading(false);
      }
    }
  }

  /**
   * Fetch real news events from backend
   */
  async fetchNewsEvents() {
    try {
      console.log('📰 Fetching real news events...');
      if (this.actions) {
        this.actions.setNewsEventsLoading(true);
      }

      const response = await apiService.getNewsEvents(24); // Next 24 hours
      const events = response.success ? response.events : [];
      
      console.log(`✅ News events fetched successfully: ${events.length} events found`);
      console.log('News events:', events);
      
      if (this.actions) {
        this.actions.setNewsEvents(events);
        this.actions.setNewsEventsError(null);
      }

      return events;
    } catch (error) {
      console.error('❌ Error fetching news events:', error);
      if (this.actions) {
        this.actions.setNewsEventsError(error.message);
        // Set empty array instead of keeping old data
        this.actions.setNewsEvents([]);
      }
      throw error;
    } finally {
      if (this.actions) {
        this.actions.setNewsEventsLoading(false);
      }
    }
  }

  /**
   * Calculate and update global statistics
   */
  async fetchGlobalStats() {
    try {
      if (this.actions) {
        this.actions.setGlobalStatsLoading(true);
      }

      // Get current EA data from context or fetch fresh
      const response = await apiService.getAllEAStatus();
      const eaData = response.eas || [];

      const stats = this.calculateGlobalStats(eaData);

      if (this.actions) {
        this.actions.setGlobalStats(stats);
        this.actions.setGlobalStatsError(null);
      }

      return stats;
    } catch (error) {
      console.error('Error calculating global stats:', error);
      if (this.actions) {
        this.actions.setGlobalStatsError(error.message);
      }
      throw error;
    } finally {
      if (this.actions) {
        this.actions.setGlobalStatsLoading(false);
      }
    }
  }

  /**
   * Calculate global statistics from EA data
   */
  calculateGlobalStats(eaData) {
    if (!eaData || eaData.length === 0) {
      return {
        totalPnL: 0,
        totalDrawdown: 0,
        winRate: 0,
        totalTrades: 0,
        activeEAs: 0,
        totalEAs: 0,
        dailyPnL: 0,
        weeklyPnL: 0
      };
    }

    const totalPnL = eaData.reduce((sum, ea) => sum + (ea.current_profit || 0), 0);
    const activeEAs = eaData.filter(ea => ea.open_positions > 0 || ea.status === 'active').length;
    const totalEAs = eaData.length;

    // Calculate average metrics (these would typically come from performance history)
    const avgWinRate = eaData.length > 0 ? 
      eaData.reduce((sum, ea) => sum + (ea.win_rate || 0), 0) / eaData.length : 0;

    return {
      totalPnL: Math.round(totalPnL * 100) / 100,
      totalDrawdown: 0, // Would need historical data
      winRate: Math.round(avgWinRate * 100) / 100,
      totalTrades: 0, // Would need trade history
      activeEAs,
      totalEAs,
      dailyPnL: 0, // Would need daily calculation
      weeklyPnL: 0 // Would need weekly calculation
    };
  }

  /**
   * Send command to EA(s)
   */
  async sendCommand(command) {
    try {
      if (this.actions) {
        this.actions.setCommandLoading(true);
      }

      let response;
      if (command.target_eas && command.target_eas.length > 1) {
        // Batch command
        response = await apiService.sendBatchCommands(command);
      } else if (command.target_eas && command.target_eas.length === 1) {
        // Single EA command
        response = await apiService.sendEACommand(command.target_eas[0], command);
      } else {
        throw new Error('No target EAs specified for command');
      }

      if (this.actions) {
        this.actions.addCommand({
          ...command,
          id: Date.now(),
          status: 'sent',
          response: response
        });
        this.actions.setCommandError(null);
      }

      return response;
    } catch (error) {
      console.error('Error sending command:', error);
      if (this.actions) {
        this.actions.setCommandError(error.message);
      }
      throw error;
    } finally {
      if (this.actions) {
        this.actions.setCommandLoading(false);
      }
    }
  }

  /**
   * Get detailed EA performance data
   */
  async getEAPerformance(magicNumber) {
    try {
      const performance = await apiService.getEAPerformance(magicNumber);
      return performance.performance_history || [];
    } catch (error) {
      console.error(`Error fetching EA ${magicNumber} performance:`, error);
      throw error;
    }
  }

  /**
   * Get EA trade history
   */
  async getEATrades(magicNumber, limit = 50) {
    try {
      const trades = await apiService.getEATrades(magicNumber, limit);
      return trades.trades || [];
    } catch (error) {
      console.error(`Error fetching EA ${magicNumber} trades:`, error);
      throw error;
    }
  }

  /**
   * Upload backtest file
   */
  async uploadBacktest(file, magicNumber) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('magic_number', magicNumber);

      const response = await apiService.uploadBacktest(formData);
      return response;
    } catch (error) {
      console.error('Error uploading backtest:', error);
      throw error;
    }
  }

  /**
   * Get backtest comparison for EA
   */
  async getBacktestComparison(magicNumber) {
    try {
      const comparison = await apiService.getBacktestComparison(magicNumber);
      return comparison;
    } catch (error) {
      console.error(`Error fetching backtest comparison for EA ${magicNumber}:`, error);
      throw error;
    }
  }

  /**
   * Check backend connectivity
   */
  async checkConnectivity() {
    try {
      console.log('🔍 Checking backend connectivity...');
      const response = await apiService.healthCheck();
      console.log('✅ Backend health check successful:', response);
      
      if (this.actions) {
        this.actions.setConnectionStatus(true);
        this.actions.setConnectionError(null);
      }
      return true;
    } catch (error) {
      console.error('❌ Backend connectivity check failed:', error);
      if (this.actions) {
        this.actions.setConnectionStatus(false);
        this.actions.setConnectionError(`Backend is not reachable: ${error.message}`);
      }
      return false;
    }
  }

  /**
   * Handle WebSocket message updates
   */
  handleWebSocketUpdate(message) {
    if (!this.actions) return;
    
    // Check if message exists and has a type property
    if (!message || typeof message !== 'object' || !message.type) {
      console.warn('Invalid WebSocket message received:', message);
      return;
    }

    switch (message.type) {
      case 'ea_update':
        this.actions.updateEAData(message.data);
        break;
      case 'portfolio_update':
        this.actions.setGlobalStats(message.data);
        break;
      case 'news_update':
        const newsEvents = message.data?.events || message.data || [];
        this.actions.setNewsEvents(newsEvents);
        break;
      case 'command_update':
        this.actions.updateCommand(message.data);
        break;
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }

  /**
   * Add update callback
   */
  onUpdate(callback) {
    this.updateCallbacks.add(callback);
    return () => this.updateCallbacks.delete(callback);
  }

  /**
   * Trigger update callbacks
   */
  triggerUpdate(data) {
    this.updateCallbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in update callback:', error);
      }
    });
  }
}

// Create singleton instance
const dashboardService = new DashboardService();

export default dashboardService;


