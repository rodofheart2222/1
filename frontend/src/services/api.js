/**
 * API Service for MT5 COC Dashboard
 * Handles all HTTP requests to the backend API
 */

import { API_BASE_URL, API_FALLBACK_URL, API_TIMEOUT } from '../config/central-config';

class APIService {
  constructor() {
    // Use centralized configuration for API URLs
    this.baseURL = API_BASE_URL;
    this.fallbackURL = API_FALLBACK_URL; 
    this.timeout = API_TIMEOUT;
    
    console.log('🔧 API Service initialized:');
    console.log(`   Base URL: ${this.baseURL}`);
    console.log(`   Fallback URL: ${this.fallbackURL}`);
    console.log(`   Timeout: ${this.timeout}ms`);
  }

  /**
   * Make HTTP request with error handling and fallback
   */
  async request(endpoint, options = {}) {
    const urls = [
      `${this.baseURL}${endpoint}`,
      `${this.fallbackURL}${endpoint}`
    ];
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    let lastError;
    
    // Try each URL in sequence
    for (const url of urls) {
      try {
        console.log(`🔍 API Request: ${url}`);
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        const response = await fetch(url, {
          ...config,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const contentType = response.headers.get('content-type');
        let result;
        if (contentType && contentType.includes('application/json')) {
          result = await response.json();
        } else {
          result = await response.text();
        }
        
        console.log(`✅ API Request successful: ${url}`, result);
        return result;
        
      } catch (error) {
        console.warn(`❌ API Request failed for ${url}:`, error.message);
        lastError = error;
        continue; // Try next URL
      }
    }
    
    // If all URLs failed, throw the last error
    console.error(`❌ All API endpoints failed for: ${endpoint}`, lastError);
    throw lastError;
  }

  /**
   * GET request
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return this.request(url, {
      method: 'GET'
    });
  }

  /**
   * POST request
   */
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }

  // EA-related API calls
  
  /**
   * Get all EA status data
   */
  async getAllEAStatus() {
    return this.get('/api/ea/status/all');
  }

  /**
   * Get specific EA status
   */
  async getEAStatus(magicNumber) {
    return this.get(`/api/ea/status/${magicNumber}`);
  }

  /**
   * Get EA performance history
   */
  async getEAPerformance(magicNumber) {
    return this.get(`/api/ea/performance/${magicNumber}`);
  }

  /**
   * Get EA trades
   */
  async getEATrades(magicNumber, limit = 50) {
    return this.get(`/api/ea/trades/${magicNumber}`, { limit });
  }

  /**
   * Send command to EA
   */
  async sendEACommand(magicNumber, command) {
    return this.post(`/api/ea/command`, {
      magic_number: magicNumber,
      ...command
    });
  }

  /**
   * Send batch commands to multiple EAs
   */
  async sendBatchCommands(command) {
    return this.post('/api/ea/commands/batch', command);
  }

  /**
   * Remove EA from system
   */
  async removeEA(magicNumber) {
    return this.delete(`/api/ea/status/${magicNumber}`);
  }

  // News-related API calls

  /**
   * Get upcoming news events
   */
  async getNewsEvents(hours = 24) {
    return this.get('/api/news/events/upcoming', { hours });
  }

  /**
   * Get active news restrictions
   */
  async getActiveRestrictions() {
    return this.get('/api/news/blackout/active');
  }

  // Backtest-related API calls

  /**
   * Upload backtest file
   */
  async uploadBacktest(formData) {
    return this.request('/api/backtest/upload', {
      method: 'POST',
      body: formData, // FormData object
      headers: {} // Let browser set Content-Type for multipart/form-data
    });
  }

  /**
   * Get backtest comparison
   */
  async getBacktestComparison(magicNumber) {
    return this.get(`/api/backtest/comparison/${magicNumber}`);
  }

  /**
   * Get performance deviation analysis
   */
  async getPerformanceDeviation(magicNumber) {
    return this.get(`/api/backtest/deviation/${magicNumber}`);
  }

  // MT5 Account-related API calls

  /**
   * Get MT5 account information
   */
  async getMT5AccountInfo() {
    return this.get('/api/mt5/account');
  }

  /**
   * Get MT5 dashboard data (includes account info and EA data)
   */
  async getMT5Dashboard() {
    return this.get('/api/mt5/dashboard');
  }

  // Health check

  /**
   * Check API health
   */
  async healthCheck() {
    return this.get('/health');
  }

  /**
   * Get API status
   */
  async getStatus() {
    return this.get('/');
  }
}

// Create singleton instance
const apiService = new APIService();

export default apiService;

// Named exports for specific functionality
export const {
  getAllEAStatus,
  getEAStatus,
  getEAPerformance,
  getEATrades,
  sendEACommand,
  sendBatchCommands,
  removeEA,
  getNewsEvents,
  getActiveRestrictions,
  uploadBacktest,
  getBacktestComparison,
  getPerformanceDeviation,
  getMT5AccountInfo,
  getMT5Dashboard,
  healthCheck,
  getStatus
} = apiService;


