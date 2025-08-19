/**
 * Connection Test Utility
 * Tests HTTP API connectivity for MT5 Dashboard
 */

import apiService from '../services/api';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';

export class ConnectionTester {
  constructor() {
    this.results = {};
    this.callbacks = [];
  }

  onUpdate(callback) {
    this.callbacks.push(callback);
  }

  notifyUpdate(message, type = 'info') {
    const update = {
      message,
      type,
      timestamp: new Date().toISOString()
    };
    
    this.callbacks.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in connection test callback:', error);
      }
    });
  }

  async testAll() {
    this.results = {};
    this.notifyUpdate('Starting comprehensive connection test...', 'info');

    // Test 1: API Connectivity
    await this.testAPI();
    
    // Test 2: WebSocket Connection
    await this.testWebSocket();
    
    // Test 3: Price Service
    await this.testPriceService();
    
    // Test 4: Real-time Updates
    await this.testRealTimeUpdates();

    return this.results;
  }

  async testAPI() {
    this.notifyUpdate('Testing API connectivity...', 'info');
    
    try {
      // Test health endpoint
      await apiService.healthCheck();
      this.results.api = { status: 'success', message: 'API is reachable' };
      this.notifyUpdate('✅ API connectivity successful', 'success');
      
      // Test EA status endpoint
      const eaStatus = await apiService.getAllEAStatus();
      this.results.eaData = { 
        status: 'success', 
        message: `Found ${eaStatus.eas?.length || 0} EAs`,
        data: eaStatus
      };
      this.notifyUpdate(`✅ EA data retrieved: ${eaStatus.eas?.length || 0} EAs`, 'success');
      
    } catch (error) {
      this.results.api = { status: 'error', message: error.message };
      this.notifyUpdate(`❌ API test failed: ${error.message}`, 'error');
    }
  }

  async testMT5Integration() {
    this.notifyUpdate('Testing MT5 integration...', 'info');
    
    try {
      // Test MT5 status endpoint
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.mt5Status}`);
      
      if (response.ok) {
        const data = await response.json();
        this.results.mt5 = { status: 'success', message: 'MT5 integration working', data: data };
        this.notifyUpdate('✅ MT5 integration successful', 'success');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      this.results.mt5 = { status: 'error', message: error.message };
      this.notifyUpdate(`❌ MT5 integration test failed: ${error.message}`, 'error');
    }
  }

  async testPriceService() {
    this.notifyUpdate('Testing price service...', 'info');
    
    try {
      // Test chart data API
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.chartData}/EURUSD`);
      
      if (response.ok) {
        const data = await response.json();
        this.results.priceService = { 
          status: 'success', 
          message: `Chart data available (${data.data?.length || 0} points)`,
          data: data
        };
        this.notifyUpdate(`✅ Price service working: ${data.source || 'API'}`, 'success');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      this.results.priceService = { status: 'error', message: error.message };
      this.notifyUpdate(`❌ Price service test failed: ${error.message}`, 'error');
    }
  }

  async testEADataUpdates() {
    this.notifyUpdate('Testing EA data updates...', 'info');
    
    try {
      // Test EA list endpoint for real-time data
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.eaList}`);
      
      if (response.ok) {
        const data = await response.json();
        this.results.realTime = { 
          status: 'success', 
          message: `Found ${data.length} EAs in system`,
          data: data
        };
        this.notifyUpdate(`✅ EA data updates working: ${data.length} EAs found`, 'success');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      this.results.realTime = { status: 'error', message: error.message };
      this.notifyUpdate(`❌ EA data updates test failed: ${error.message}`, 'error');
    }
  }

  getResults() {
    return this.results;
  }

  getSummary() {
    const tests = Object.keys(this.results);
    const passed = tests.filter(test => this.results[test].status === 'success').length;
    const warnings = tests.filter(test => this.results[test].status === 'warning').length;
    const failed = tests.filter(test => this.results[test].status === 'error').length;

    return {
      total: tests.length,
      passed,
      warnings,
      failed,
      success: failed === 0
    };
  }
}

// Export singleton instance
export const connectionTester = new ConnectionTester();

// Quick test functions
export const quickAPITest = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.health}`);
    const success = response.ok;
    return { 
      success, 
      message: success ? 'Backend API connected' : 'Backend API connection failed'
    };
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export default connectionTester;