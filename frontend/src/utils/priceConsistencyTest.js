/**
 * Price Consistency Test Utility
 * Tests that all components are using the same centralized prices
 */

import chartService from '../services/chartService';

export const testPriceConsistency = () => {
  console.log('🔍 Testing price consistency across components...');
  
  const testSymbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD'];
  const results = {
    centralizedPrices: {},
    tickerPrices: {},
    chartPrices: {},
    inconsistencies: []
  };

  // Get centralized prices
  console.log('📊 Getting centralized prices from chartService...');
  testSymbols.forEach(symbol => {
    results.centralizedPrices[symbol] = chartService.getCurrentPrice(symbol);
  });

  // Get ticker prices
  console.log('📈 Getting ticker prices...');
  const tickerData = chartService.getTickerData(testSymbols);
  tickerData.forEach(item => {
    results.tickerPrices[item.symbol] = item.price;
  });

  // Test chart data prices
  console.log('📉 Testing chart data prices...');
  const testChartData = async () => {
    for (const symbol of testSymbols) {
      try {
        const chartData = await chartService.getChartData(symbol, '1H', 10);
        results.chartPrices[symbol] = chartData.current_price;
      } catch (error) {
        console.warn(`Failed to get chart data for ${symbol}:`, error);
        results.chartPrices[symbol] = 'ERROR';
      }
    }

    // Check for inconsistencies
    console.log('🔍 Checking for inconsistencies...');
    testSymbols.forEach(symbol => {
      const centralPrice = results.centralizedPrices[symbol];
      const tickerPrice = results.tickerPrices[symbol];
      const chartPrice = results.chartPrices[symbol];

      if (centralPrice !== tickerPrice) {
        results.inconsistencies.push({
          symbol,
          type: 'centralized vs ticker',
          centralized: centralPrice,
          ticker: tickerPrice
        });
      }

      if (centralPrice !== chartPrice && chartPrice !== 'ERROR') {
        results.inconsistencies.push({
          symbol,
          type: 'centralized vs chart',
          centralized: centralPrice,
          chart: chartPrice
        });
      }
    });

    // Display results
    console.log('📋 Price Consistency Test Results:');
    console.table(results.centralizedPrices);
    
    if (results.inconsistencies.length === 0) {
      console.log('✅ All prices are consistent!');
    } else {
      console.log('❌ Found inconsistencies:');
      console.table(results.inconsistencies);
    }

    return results;
  };

  return testChartData();
};

// Make it available globally for console testing
if (typeof window !== 'undefined') {
  window.testPriceConsistency = testPriceConsistency;
}