/**
 * Connection Test Utility
 * Tests WebSocket and API connectivity
 */

import webSocketService from '../services/webSocketService';
import apiService from '../services/api';

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

  async testWebSocket() {
    this.notifyUpdate('Testing WebSocket connection...', 'info');
    
    try {
      // Test connection
      await webSocketService.connect();
      
      if (webSocketService.isConnected) {
        this.results.websocket = { status: 'success', message: 'WebSocket connected' };
        this.notifyUpdate('✅ WebSocket connection successful', 'success');
      } else {
        throw new Error('WebSocket connection failed');
      }
      
    } catch (error) {
      this.results.websocket = { status: 'error', message: error.message };
      this.notifyUpdate(`❌ WebSocket test failed: ${error.message}`, 'error');
    }
  }

  async testPriceService() {
    this.notifyUpdate('Testing price service...', 'info');
    
    try {
      // Test chart data API
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'}/api/ea/chart-data/EURUSD`);
      
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

  async testRealTimeUpdates() {
    this.notifyUpdate('Testing real-time updates...', 'info');
    
    return new Promise((resolve) => {
      if (!webSocketService.isConnected) {
        this.results.realTime = { status: 'error', message: 'WebSocket not connected' };
        this.notifyUpdate('❌ Real-time test skipped: WebSocket not connected', 'error');
        resolve();
        return;
      }

      let receivedUpdates = false;
      
      // Subscribe to price updates
      const unsubscribe = webSocketService.subscribe('price_update', (data) => {
        receivedUpdates = true;
        this.results.realTime = { 
          status: 'success', 
          message: `Received updates for ${Object.keys(data).length} symbols`,
          data: data
        };
        this.notifyUpdate(`✅ Real-time updates working: ${Object.keys(data).length} symbols`, 'success');
      });

      // Subscribe to test symbols
      webSocketService.subscribeToPrices(['EURUSD', 'GBPUSD', 'XAUUSD']);
      this.notifyUpdate('Subscribed to test symbols, waiting for updates...', 'info');

      // Wait for updates with timeout
      setTimeout(() => {
        unsubscribe();
        
        if (!receivedUpdates) {
          this.results.realTime = { status: 'warning', message: 'No real-time updates received' };
          this.notifyUpdate('⚠️ No real-time updates received within timeout', 'warning');
        }
        
        resolve();
      }, 5000); // 5 second timeout
    });
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
    await apiService.healthCheck();
    return { success: true, message: 'API is reachable' };
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export const quickWebSocketTest = async () => {
  try {
    await webSocketService.connect();
    return { 
      success: webSocketService.isConnected, 
      message: webSocketService.isConnected ? 'WebSocket connected' : 'WebSocket connection failed'
    };
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export default connectionTester;