/**
 * Test WebSocket Price Updates
 * Simple test to verify price updates are working
 */

export const testWebSocketPrices = () => {
  return new Promise((resolve) => {
    console.log('🔍 Testing WebSocket price updates...');
    
    const ws = new WebSocket('ws://155.138.174.196:8765');
    const results = {
      connected: false,
      authenticated: false,
      subscribed: false,
      priceUpdatesReceived: 0,
      messages: []
    };
    
    const timeout = setTimeout(() => {
      ws.close();
      resolve({
        success: false,
        error: 'Test timeout',
        results
      });
    }, 15000); // 15 second timeout
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      results.connected = true;
      
      // Send authentication
      const authMessage = {
        type: 'auth',
        data: { token: 'dashboard_token' }
      };
      ws.send(JSON.stringify(authMessage));
      console.log('📤 Sent authentication');
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        results.messages.push(message);
        console.log('📥 Received message:', message);
        
        if (message.type === 'auth_response') {
          if (message.data.status === 'authenticated') {
            console.log('✅ Authentication successful');
            results.authenticated = true;
            
            // First subscribe to the price_updates channel
            const channelSubMessage = {
              type: 'subscribe',
              data: { channels: ['price_updates'] }
            };
            ws.send(JSON.stringify(channelSubMessage));
            console.log('📤 Sent channel subscription');
            
            // Then subscribe to price updates for specific symbols
            const priceSubMessage = {
              type: 'subscribe_prices',
              data: { symbols: ['EURUSD', 'GBPUSD'] }
            };
            ws.send(JSON.stringify(priceSubMessage));
            console.log('📤 Sent price subscription');
          } else {
            console.error('❌ Authentication failed:', message.data.message);
          }
        }
        
        if (message.type === 'price_subscription_response') {
          console.log('✅ Price subscription confirmed:', message.data);
          results.subscribed = true;
        }
        
        if (message.type === 'price_update') {
          console.log('📈 Price update received:', message.data);
          results.priceUpdatesReceived++;
          
          // If we've received price updates, test is successful
          if (results.priceUpdatesReceived >= 1) {
            clearTimeout(timeout);
            ws.close();
            resolve({
              success: true,
              results
            });
          }
        }
        
        // If we've been waiting for 10 seconds after subscription, consider it done
        if (results.subscribed && results.messages.length > 3) {
          setTimeout(() => {
            clearTimeout(timeout);
            ws.close();
            resolve({
              success: results.priceUpdatesReceived > 0,
              results
            });
          }, 5000);
        }
        
      } catch (error) {
        console.error('❌ Error parsing message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      clearTimeout(timeout);
      resolve({
        success: false,
        error: 'WebSocket connection error',
        results
      });
    };
    
    ws.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      clearTimeout(timeout);
    };
  });
};

// Test function that can be called from console
window.testWebSocketPrices = testWebSocketPrices;