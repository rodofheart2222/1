/**
 * API Configuration
 * DEPRECATED: This file is deprecated. Use './central-config.js' instead.
 * All configuration now comes from the central config.json file in the project root.
 */

// Import from central configuration
import centralConfig, {
  API_BASE_URL,
  API_FALLBACK_URL,
  FRONTEND_DEV_URL,
  API_TIMEOUT,
  API_ENDPOINTS
} from './central-config';

// Export for backward compatibility
export {
  API_BASE_URL,
  API_FALLBACK_URL,
  FRONTEND_DEV_URL,
  API_TIMEOUT,
  API_ENDPOINTS
};

// Default export for easy importing (backward compatibility)
export default centralConfig;
