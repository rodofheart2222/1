const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimizeWindow: () => ipcRenderer.invoke('window-minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window-maximize'),
  closeWindow: () => ipcRenderer.invoke('window-close'),
  isWindowMaximized: () => ipcRenderer.invoke('window-is-maximized'),
  
  // App info
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  
  // Notifications
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body),
  
  // Development
  openDevTools: () => ipcRenderer.invoke('open-devtools'),
  
  // WebSocket management
  connectWebSocket: (url) => ipcRenderer.invoke('websocket-connect', url),
  disconnectWebSocket: () => ipcRenderer.invoke('websocket-disconnect'),
  sendWebSocketMessage: (data) => ipcRenderer.invoke('websocket-send', data),
  
  // WebSocket message listener
  onWebSocketMessage: (callback) => {
    ipcRenderer.on('websocket-message', (event, message) => {
      callback(message);
    });
  },
  
  // Remove WebSocket message listener
  removeWebSocketListener: () => {
    ipcRenderer.removeAllListeners('websocket-message');
  }
});

// Platform info
contextBridge.exposeInMainWorld('platform', {
  isElectron: true,
  platform: process.platform,
  arch: process.arch,
  versions: process.versions
});