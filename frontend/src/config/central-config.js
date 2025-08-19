/**
 * Central Configuration Loader
 * Loads configuration from root config.json file
 */

import configData from '../config.json';

// ==========================================
// CONFIGURATION LOADER
// ==========================================

const config = configData;

// ==========================================
// BACKEND CONFIGURATION
// ==========================================

// Primary API URL - checks environment variable first, then central config
export const API_BASE_URL = process.env.REACT_APP_API_URL || config.backend?.base_url || 'http://127.0.0.1:80';

// Fallback URL
export const API_FALLBACK_URL = process.env.REACT_APP_API_FALLBACK_URL || API_BASE_URL;

// ==========================================
// FRONTEND CONFIGURATION
// ==========================================

// Frontend development URL
export const FRONTEND_DEV_URL = config.frontend?.dev?.url || 'http://127.0.0.1:3000';

// Frontend production URL  
export const FRONTEND_PROD_URL = config.frontend?.prod?.url || 'http://127.0.0.1:80';

// ==========================================
// WEBSOCKET CONFIGURATION
// ==========================================

// WebSocket URL
export const WS_URL = process.env.REACT_APP_WS_URL || config.websocket?.url || 'ws://127.0.0.1:8765';

// ==========================================
// API CONFIGURATION
// ==========================================

// Timeout settings
export const API_TIMEOUT = config.api?.timeout || 15000;

// API endpoints from central config
export const API_ENDPOINTS = {
  health: config.api?.endpoints?.health || '/health',
  eaStatus: config.api?.endpoints?.ea_status || '/api/ea/status/all',
  eaList: config.api?.endpoints?.ea_list || '/api/ea/list',
  mt5Status: config.api?.endpoints?.mt5_status || '/api/mt5/status',
  newsEvents: config.api?.endpoints?.news_events || '/api/news/events/upcoming',
  chartData: config.api?.endpoints?.chart_data || '/api/ea/chart-data'
};

// ==========================================
// CORS CONFIGURATION
// ==========================================

// CORS origins (mainly for reference in frontend)
export const CORS_ORIGINS = {
  development: config.cors?.development || [],
  production: config.cors?.production || []
};

// ==========================================
// EXTERNAL API CONFIGURATION
// ==========================================

// News API configuration (for reference)
export const NEWS_API_CONFIG = {
  baseUrl: config.external_apis?.news?.base_url || 'https://api.forexfactory.com',
  calendarEndpoint: config.external_apis?.news?.calendar_endpoint || '/calendar',
  fullUrl: config.external_apis?.news?.full_url || 'https://api.forexfactory.com/calendar'
};

// ==========================================
// HELPER FUNCTIONS
// ==========================================

/**
 * Get the full configuration object
 */
export const getConfig = () => config;

/**
 * Get API URL with endpoint
 */
export const getApiUrl = (endpoint) => {
  if (endpoint.startsWith('/')) {
    return `${API_BASE_URL}${endpoint}`;
  }
  return `${API_BASE_URL}/${endpoint}`;
};

/**
 * Get WebSocket URL  
 */
export const getWebSocketUrl = () => WS_URL;

/**
 * Check if running in development mode
 */
export const isDevelopment = () => {
  return process.env.NODE_ENV === 'development';
};

/**
 * Check if running in production mode
 */
export const isProduction = () => {
  return process.env.NODE_ENV === 'production';
};

// ==========================================
// DEFAULT EXPORT
// ==========================================

// Default export for easy importing
export default {
  API_BASE_URL,
  API_FALLBACK_URL,
  FRONTEND_DEV_URL,
  FRONTEND_PROD_URL,
  WS_URL,
  API_TIMEOUT,
  API_ENDPOINTS,
  CORS_ORIGINS,
  NEWS_API_CONFIG,
  getConfig,
  getApiUrl,
  getWebSocketUrl,
  isDevelopment,
  isProduction
};
