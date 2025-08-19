/**
 * Chart Service
 * Handles fetching price chart data from the backend
 */

import { API_BASE_URL } from '../config/api';

class ChartService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 60000; // 1 minute cache

    // Real-time current prices - updated from WebSocket/API
    // All components (TickerBar, PriceChart, MiniChart, etc.) should use these prices
    // to ensure consistency across the entire application
    this.currentPrices = {};

    // Initialize with empty prices - will be populated from real data sources
    this.initializePrices();
  }

  /**
   * Initialize prices from backend API
   */
  async initializePrices() {
    try {
      // Try to get initial prices from backend
      const response = await fetch(`${API_BASE_URL}/api/ea/current-prices`);
      if (response.ok) {
        const priceData = await response.json();
        this.currentPrices = priceData.prices || {};
        console.log('✅ Initialized prices from backend API');
      } else {
        // Fallback to default values only if API fails
        this.currentPrices = {
          'EURUSD': 1.0847,
          'GBPUSD': 1.2634,
          'USDJPY': 149.82,
          'USDCHF': 0.8756,
          'AUDUSD': 0.6523,
          'USDCAD': 1.3789,
          'NZDUSD': 0.5987,
          'XAUUSD': 2034.67
        };
        console.log('⚠️ Using fallback prices - backend API not available');
      }
    } catch (error) {
      console.error('❌ Failed to initialize prices from backend:', error);
      // Use fallback prices
      this.currentPrices = {
        'EURUSD': 1.0847,
        'GBPUSD': 1.2634,
        'USDJPY': 149.82,
        'USDCHF': 0.8756,
        'AUDUSD': 0.6523,
        'USDCAD': 1.3789,
        'NZDUSD': 0.5987,
        'XAUUSD': 2034.67
      };
    }
  }

  /**
   * Get price chart data for a symbol
   */
  async getChartData(symbol, timeframe = '1H', points = 50) {
    const cacheKey = `${symbol}_${timeframe}_${points}`;

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      console.log(`📊 Using cached chart data for ${symbol}`);
      return cached.data;
    }

    try {
      console.log(`📈 Fetching real chart data for ${symbol} (${timeframe}, ${points} points)`);

      const response = await fetch(
        `${API_BASE_URL}/api/ea/chart-data/${symbol}?timeframe=${timeframe}&points=${points}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Cache the real data
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      // Update current price from real data
      if (data.current_price) {
        this.currentPrices[symbol.toUpperCase()] = data.current_price;
      }

      console.log(`✅ Real chart data fetched for ${symbol}:`, data.source || 'MT5/API');
      return data;
    } catch (error) {
      console.error(`❌ Failed to fetch real chart data for ${symbol}:`, error);

      // Only use fallback if absolutely necessary
      console.log(`🔄 Using fallback data for ${symbol} - backend unavailable`);
      return this.generateMockData(symbol, timeframe, points);
    }
  }

  /**
   * Generate fallback chart data only when backend is completely unavailable
   */
  generateMockData(symbol, timeframe = '1H', points = 50) {
    console.warn(`⚠️ Using fallback chart data for ${symbol} - backend unavailable`);

    const currentPrice = this.getCurrentPrice(symbol) || 1.0000;
    const data = [];
    const now = new Date();

    // Timeframe intervals in minutes
    const intervals = {
      '1M': 1,
      '5M': 5,
      '15M': 15,
      '1H': 60,
      '4H': 240,
      '1D': 1440
    };

    const intervalMinutes = intervals[timeframe] || 60;

    // Generate minimal fallback data
    let price = currentPrice;

    for (let i = points - 1; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * intervalMinutes * 60 * 1000);

      // Minimal price variation for fallback
      const variation = (Math.random() - 0.5) * 0.001; // Very small variation
      price = currentPrice * (1 + variation * (i / points));

      data.push({
        timestamp: timestamp.toISOString(),
        open: parseFloat(price.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
        high: parseFloat((price * 1.001).toFixed(symbol === 'XAUUSD' ? 2 : 5)),
        low: parseFloat((price * 0.999).toFixed(symbol === 'XAUUSD' ? 2 : 5)),
        close: parseFloat(price.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
        volume: 100000
      });
    }

    // Sort data by timestamp
    data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    const priceChange = data.length >= 2 ? data[data.length - 1].close - data[data.length - 2].close : 0;

    return {
      symbol: symbol.toUpperCase(),
      timeframe,
      data,
      current_price: currentPrice,
      price_change: parseFloat(priceChange.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
      last_update: now.toISOString(),
      source: 'fallback_only'
    };
  }

  /**
   * Get current price for a symbol (consistent across all components)
   */
  getCurrentPrice(symbol) {
    return this.currentPrices[symbol.toUpperCase()] || 1.0000;
  }

  /**
   * Get all current prices
   */
  getAllCurrentPrices() {
    return { ...this.currentPrices };
  }

  /**
   * Update a price (for future real-time updates)
   */
  updatePrice(symbol, price) {
    this.currentPrices[symbol.toUpperCase()] = price;
  }

  /**
   * Update multiple prices at once (useful for WebSocket batch updates)
   */
  updatePrices(priceUpdates) {
    Object.entries(priceUpdates).forEach(([symbol, price]) => {
      this.currentPrices[symbol.toUpperCase()] = price;
    });
  }

  /**
   * Get ticker market data from real sources
   */
  async getTickerData(symbols) {
    try {
      // Try to get real ticker data from backend
      const response = await fetch(`${API_BASE_URL}/api/ea/ticker-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbols })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Real ticker data fetched from backend');

        // Update current prices from real data
        data.forEach(item => {
          if (item.price) {
            this.currentPrices[item.symbol.toUpperCase()] = item.price;
          }
        });

        return data;
      }
    } catch (error) {
      console.error('❌ Failed to fetch real ticker data:', error);
    }

    // Fallback to current prices with calculated changes
    console.log('🔄 Using fallback ticker data');
    return symbols.map(symbol => {
      const currentPrice = this.getCurrentPrice(symbol);

      // Create realistic hourly change based on symbol and time
      const symbolSeed = symbol.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const timeFactor = Math.sin(Date.now() / 300000); // 5-minute cycles
      const changePercent = (Math.sin(symbolSeed / 100) * 0.8 + timeFactor * 0.3); // ±0.8% max change
      const hourlyChange = currentPrice * (changePercent / 100);

      return {
        symbol,
        price: currentPrice,
        change: hourlyChange,
        changePercent: changePercent,
        volume: Math.floor((symbolSeed * 12345) % 1000000) + 100000,
        source: 'fallback_calculated'
      };
    });
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Get multiple symbols data
   */
  async getMultipleChartData(symbols, timeframe = '1H', points = 50) {
    const promises = symbols.map(symbol =>
      this.getChartData(symbol, timeframe, points)
    );

    try {
      const results = await Promise.all(promises);
      return results.reduce((acc, data, index) => {
        acc[symbols[index]] = data;
        return acc;
      }, {});
    } catch (error) {
      console.error('Failed to fetch multiple chart data:', error);
      return {};
    }
  }
}

// Export singleton instance
const chartService = new ChartService();
export default chartService;