/**
 * WebSocket Service for MT5 COC Dashboard
 * Handles WebSocket connections with automatic reconnection and error handling
 */

class WebSocketService {
  constructor() {
    this.websocket = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.manualDisconnect = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 15; // Reduced from 10
    this.reconnectDelay = 2000; // Start with 2 seconds instead of 1
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.heartbeatInterval = null;
    this.heartbeatTimer = 30000; // 30 seconds
    this.messageQueue = [];
    this.callbacks = new Map();

    // Event handlers
    this.onConnectionChange = null;
    this.onMessage = null;
    this.onError = null;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(url = 'ws://155.138.174.196:8765') {
    if (this.isConnecting || this.isConnected) {
      return Promise.resolve();
    }

    this.manualDisconnect = false; // Reset manual disconnect flag
    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        // Always use direct WebSocket connection for web version
        // Electron API handling can be added later if needed
        this.connectDirectly(url, resolve, reject);
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Connect via Electron API
   */
  connectViaElectron(url, resolve, reject) {
    window.electronAPI.connectWebSocket(url)
      .then(result => {
        if (result && result.success) {
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.setupElectronMessageHandlers();
          this.flushMessageQueue();
          this.notifyConnectionChange(true);
          console.log(' WebSocket connected via Electron API');
          resolve();
        } else {
          this.isConnecting = false;
          const errorMsg = result?.message || 'Failed to connect to WebSocket server. Please ensure the backend server is running.';
          console.error(' Electron WebSocket connection failed:', errorMsg);
          reject(new Error(errorMsg));
        }
      })
      .catch(error => {
        this.isConnecting = false;
        const errorMsg = error?.message || 'WebSocket connection failed - please check if backend server is running';
        console.error(' Electron WebSocket error:', error);
        reject(new Error(errorMsg));
      });
  }

  /**
   * Connect directly (for web version)
   */
  connectDirectly(url, resolve, reject) {
    try {
      this.websocket = new WebSocket(url);

      this.websocket.onopen = () => {
        console.log('🔌 WebSocket connected directly');
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        // Send authentication immediately after connection
        console.log('🔐 Sending authentication...');
        this.sendMessage({
          type: 'auth',
          data: {
            token: 'dashboard_token'
          }
        });
        
        this.startHeartbeat();
        this.flushMessageQueue();
        this.notifyConnectionChange(true);
        resolve();
      };

      this.websocket.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.websocket.onclose = (event) => {
        console.warn(`🔌 WebSocket closed: ${event.code} - ${event.reason}`);
        this.handleDisconnection();
      };

      this.websocket.onerror = (error) => {
        this.isConnecting = false;
        const errorMsg = 'WebSocket connection failed - please ensure the backend WebSocket server is running on port 8765';
        console.error('❌ Direct WebSocket error:', error);
        this.handleError(new Error(errorMsg));
        reject(new Error(errorMsg));
      };
    } catch (error) {
      this.isConnecting = false;
      const errorMsg = `Failed to create WebSocket connection: ${error.message}`;
      console.error('❌ WebSocket creation error:', error);
      reject(new Error(errorMsg));
    }
  }

  /**
   * Setup Electron message handlers
   */
  setupElectronMessageHandlers() {
    if (window.electronAPI) {
      window.electronAPI.onWebSocketMessage((event, data) => {
        this.handleMessage(data);
      });
    }
  }

  /**
   * Handle incoming messages
   */
  handleMessage(data) {
    try {
      // Check if data exists
      if (!data) {
        console.warn('Received empty WebSocket message');
        return;
      }

      const message = typeof data === 'string' ? JSON.parse(data) : data;

      // Check if message is valid and has a type
      if (!message || typeof message !== 'object' || !message.type) {
        console.warn('Invalid WebSocket message format:', message);
        return;
      }

      console.log('📥 WebSocket message received:', message.type, message);

      // Handle authentication responses
      if (message.type === 'auth_response') {
        console.log('🔐 Authentication response:', message.data);
        if (message.data.status === 'authenticated') {
          console.log('✅ WebSocket authenticated successfully');
          // Subscribe to real-time channels after authentication
          this.subscribeToRealTimeChannels();
        }
        return;
      }

      // Handle connection messages
      if (message.type === 'connection') {
        console.log('🔌 Connection message:', message.data);
        return;
      }

      // Handle price subscription responses
      if (message.type === 'price_subscription_response') {
        console.log('📈 Price subscription response:', message.data);
        if (message.data.status === 'subscribed') {
          console.log('✅ Successfully subscribed to price updates for:', message.data.symbols);
        }
        return;
      }

      // Handle heartbeat responses
      if (message.type === 'heartbeat_response') {
        console.debug('💓 Heartbeat acknowledged');
        return;
      }

      // Handle connection status
      if (message.type === 'connection_status') {
        this.notifyConnectionChange(message.connected);
        return;
      }

      // Notify message handler
      if (this.onMessage) {
        this.onMessage(message);
      }

      // Trigger specific callbacks
      const callbacks = this.callbacks.get(message.type);
      if (callbacks) {
        if (Array.isArray(callbacks)) {
          // Call all callbacks for this message type
          callbacks.forEach(callback => {
            try {
              callback(message.data);
            } catch (error) {
              console.error(`Error in callback for ${message.type}:`, error);
            }
          });
        } else {
          // Single callback (backward compatibility)
          try {
            callbacks(message.data);
          } catch (error) {
            console.error(`Error in callback for ${message.type}:`, error);
          }
        }
      }

    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      if (this.onError) {
        this.onError(error);
      }
    }
  }

  /**
   * Handle disconnection
   */
  handleDisconnection() {
    this.isConnected = false;
    this.stopHeartbeat();
    this.notifyConnectionChange(false);

    // Only attempt to reconnect if we haven't exceeded max attempts and it wasn't a manual disconnect
    if (this.reconnectAttempts < this.maxReconnectAttempts && !this.manualDisconnect) {
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      if (this.onError) {
        this.onError(new Error('Max reconnection attempts reached'));
      }
    }
  }

  /**
   * Handle errors
   */
  handleError(error) {
    const errorMessage = error?.message || error?.toString() || 'Unknown WebSocket error';
    console.error('WebSocket error:', errorMessage);

    if (this.onError) {
      this.onError(new Error(errorMessage));
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      if (!this.isConnected && !this.isConnecting) {
        this.reconnectAttempts++;
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  /**
   * Start heartbeat
   */
  startHeartbeat() {
    this.stopHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.sendMessage({
          type: 'heartbeat',
          data: {
            client_time: Date.now(),
            client_id: 'dashboard_frontend'
          }
        });
      }
    }, this.heartbeatTimer);
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Send message
   */
  sendMessage(message) {
    const messageStr = JSON.stringify(message);

    if (!this.isConnected) {
      // Queue message for later
      this.messageQueue.push(messageStr);
      return false;
    }

    try {
      if (window.electronAPI) {
        window.electronAPI.sendWebSocketMessage(message);
      } else if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send(messageStr);
      } else {
        this.messageQueue.push(messageStr);
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error sending message:', error);
      this.messageQueue.push(messageStr);
      return false;
    }
  }

  /**
   * Flush queued messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      try {
        if (window.electronAPI) {
          window.electronAPI.sendWebSocketMessage(JSON.parse(message));
        } else if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.send(message);
        } else {
          // Put it back if we can't send it
          this.messageQueue.unshift(message);
          break;
        }
      } catch (error) {
        console.error('Error flushing message:', error);
      }
    }
  }

  /**
   * Subscribe to message type
   */
  subscribe(messageType, callback) {
    // Support multiple callbacks for the same message type
    if (!this.callbacks.has(messageType)) {
      this.callbacks.set(messageType, []);
    }
    
    const callbacks = this.callbacks.get(messageType);
    if (Array.isArray(callbacks)) {
      callbacks.push(callback);
    } else {
      // Convert single callback to array for backward compatibility
      this.callbacks.set(messageType, [callbacks, callback]);
    }

    // Send subscription message if connected
    if (this.isConnected) {
      this.sendMessage({
        type: 'subscribe',
        data: {
          channels: [messageType]
        }
      });
    }

    // Return unsubscribe function
    return () => {
      const callbacks = this.callbacks.get(messageType);
      if (Array.isArray(callbacks)) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
        // Remove the message type entirely if no callbacks left
        if (callbacks.length === 0) {
          this.callbacks.delete(messageType);
          
          if (this.isConnected) {
            this.sendMessage({
              type: 'unsubscribe',
              data: {
                channels: [messageType]
              }
            });
          }
        }
      } else {
        // Single callback case
        this.callbacks.delete(messageType);
        
        if (this.isConnected) {
          this.sendMessage({
            type: 'unsubscribe',
            data: {
              channels: [messageType]
            }
          });
        }
      }
    };
  }

  /**
   * Subscribe to real-time channels after authentication
   */
  subscribeToRealTimeChannels() {
    console.log('📡 Subscribing to real-time data channels...');
    
    // Subscribe to all important channels
    const channels = [
      'ea_updates',
      'portfolio_updates', 
      'price_updates',
      'news_updates',
      'command_updates',
      'trade_updates'
    ];
    
    this.sendMessage({
      type: 'subscribe',
      data: {
        channels: channels
      }
    });
    
    // Subscribe to major currency pairs for price updates
    const majorSymbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD'];
    this.subscribeToPrices(majorSymbols);
  }

  /**
   * Subscribe to price updates for symbols
   */
  subscribeToPrices(symbols) {
    console.log('📈 Subscribing to real MT5 price updates for symbols:', symbols);
    console.log('🔌 WebSocket connected:', this.isConnected);
    
    if (this.isConnected) {
      const success = this.sendMessage({
        type: 'subscribe_prices',
        data: {
          symbols: symbols
        }
      });
      console.log('📤 Real price subscription message sent:', success);
    } else {
      console.log('⏳ Queueing real price subscription for when connected');
      // Queue the subscription for when we connect
      this.messageQueue.push(JSON.stringify({
        type: 'subscribe_prices',
        data: {
          symbols: symbols
        }
      }));
    }
  }

  /**
   * Request chart data for a symbol
   */
  requestChartData(symbol, timeframe = '1H', points = 50) {
    return new Promise((resolve, reject) => {
      if (!this.isConnected) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      // Create a temporary callback for this request
      const requestId = `chart_${symbol}_${Date.now()}`;
      const timeout = setTimeout(() => {
        // Handle both single callback and array of callbacks
        const callbacks = this.callbacks.get('chart_data_response');
        if (callbacks) {
          this.callbacks.delete('chart_data_response');
        }
        reject(new Error('Chart data request timeout'));
      }, 10000); // 10 second timeout

      const responseCallback = (data) => {
        clearTimeout(timeout);
        // Handle both single callback and array of callbacks
        const callbacks = this.callbacks.get('chart_data_response');
        if (callbacks) {
          this.callbacks.delete('chart_data_response');
        }

        if (data.symbol === symbol) {
          resolve(data.data);
        }
      };

      // For one-time requests like chart data, we can override the callback
      this.callbacks.set('chart_data_response', responseCallback);

      this.sendMessage({
        type: 'get_chart_data',
        data: {
          symbol: symbol,
          timeframe: timeframe,
          points: points,
          request_id: requestId
        }
      });
    });
  }

  /**
   * Notify connection status change
   */
  notifyConnectionChange(connected) {
    if (this.onConnectionChange) {
      this.onConnectionChange(connected);
    }
  }

  /**
   * Disconnect
   */
  disconnect() {
    this.manualDisconnect = true; // Flag to prevent automatic reconnection
    this.isConnected = false;
    this.isConnecting = false;
    this.stopHeartbeat();

    if (window.electronAPI) {
      window.electronAPI.disconnectWebSocket();
    } else if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    this.notifyConnectionChange(false);
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length
    };
  }

  /**
   * Reset connection state
   */
  reset() {
    this.disconnect();
    this.reconnectAttempts = 0;
    this.messageQueue = [];
    this.callbacks.clear();
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();

export default webSocketService;
