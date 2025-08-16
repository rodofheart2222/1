/**
 * Ticker WebSocket Integration Test
 * Tests that the TickerBar is properly receiving MT5 price data via WebSocket
 */

import webSocketService from '../services/webSocketService';

export const testTickerWebSocketIntegration = async () => {
  console.log('🔍 Testing TickerBar WebSocket integration...');
  
  const testResults = {
    connectionStatus: false,
    priceUpdatesReceived: 0,
    symbolsReceived: [],
    testDuration: 10000, // 10 seconds
    startTime: Date.now()
  };

  try {
    // Check initial connection status
    const status = webSocketService.getConnectionStatus();
    console.log('📊 Initial WebSocket status:', status);
    testResults.connectionStatus = status.isConnected;

    if (!status.isConnected) {
      console.log('🔌 Attempting to connect to WebSocket...');
      await webSocketService.connect();
      testResults.connectionStatus = webSocketService.getConnectionStatus().isConnected;
    }

    if (!testResults.connectionStatus) {
      console.error('❌ Failed to establish WebSocket connection');
      return testResults;
    }

    console.log('✅ WebSocket connected, subscribing to price updates...');

    // Subscribe to price updates
    const unsubscribe = webSocketService.subscribe('price_update', (priceData) => {
      testResults.priceUpdatesReceived++;
      const symbols = Object.keys(priceData);
      
      // Track unique symbols received
      symbols.forEach(symbol => {
        if (!testResults.symbolsReceived.includes(symbol)) {
          testResults.symbolsReceived.push(symbol);
        }
      });

      console.log(`📈 Price update #${testResults.priceUpdatesReceived}:`, {
        symbols: symbols.length,
        sampleData: symbols.slice(0, 3).map(s => ({
          symbol: s,
          price: priceData[s].price,
          bid: priceData[s].bid,
          ask: priceData[s].ask
        }))
      });
    });

    // Subscribe to ticker symbols
    const tickerSymbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD'];
    webSocketService.subscribeToPrices(tickerSymbols);

    console.log(`⏱️ Testing for ${testResults.testDuration / 1000} seconds...`);

    // Wait for test duration
    await new Promise(resolve => setTimeout(resolve, testResults.testDuration));

    // Cleanup
    unsubscribe();

    // Calculate results
    const endTime = Date.now();
    const actualDuration = endTime - testResults.startTime;
    const updatesPerSecond = testResults.priceUpdatesReceived / (actualDuration / 1000);

    console.log('📋 Test Results:');
    console.log(`✅ Connection Status: ${testResults.connectionStatus ? 'Connected' : 'Disconnected'}`);
    console.log(`📊 Price Updates Received: ${testResults.priceUpdatesReceived}`);
    console.log(`📈 Updates per Second: ${updatesPerSecond.toFixed(2)}`);
    console.log(`🎯 Symbols Received: ${testResults.symbolsReceived.length} (${testResults.symbolsReceived.join(', ')})`);
    console.log(`⏱️ Test Duration: ${(actualDuration / 1000).toFixed(1)}s`);

    // Determine test success
    const isSuccess = testResults.connectionStatus && 
                     testResults.priceUpdatesReceived > 0 && 
                     testResults.symbolsReceived.length > 0;

    if (isSuccess) {
      console.log('🎉 WebSocket integration test PASSED!');
    } else {
      console.log('❌ WebSocket integration test FAILED');
    }

    testResults.success = isSuccess;
    testResults.updatesPerSecond = updatesPerSecond;
    testResults.actualDuration = actualDuration;

    return testResults;

  } catch (error) {
    console.error('❌ Error during WebSocket integration test:', error);
    testResults.error = error.message;
    return testResults;
  }
};

// Make it available globally for console testing
if (typeof window !== 'undefined') {
  window.testTickerWebSocket = testTickerWebSocketIntegration;
}

export default testTickerWebSocketIntegration;