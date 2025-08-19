const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
// Simple development check instead of electron-is-dev
const isDev = process.env.NODE_ENV === 'development' || process.defaultApp || /[\\/]electron-prebuilt[\\/]/.test(process.execPath) || /[\\/]electron[\\/]/.test(process.execPath);

let mainWindow;
let backendProcess = null;

function startBackendServer() {
  if (isDev) {
    console.log('Development mode - backend should be started manually');
    return;
  }

  try {
    const fs = require('fs');
    const isWindows = process.platform === 'win32';
    const backendExe = isWindows ? 'mt5-backend.exe' : 'mt5-backend';
    const backendPath = path.join(process.resourcesPath, 'backend', backendExe);

    // Check if backend executable exists
    if (!fs.existsSync(backendPath)) {
      console.log('Backend executable not found at:', backendPath);
      console.log('Running in frontend-only mode');
      return;
    }

    console.log('Starting backend server:', backendPath);

    backendProcess = spawn(backendPath, [], {
      cwd: path.join(process.resourcesPath, 'backend'),
      stdio: 'pipe'
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend process:', error);
      backendProcess = null;
    });

    backendProcess.stdout.on('data', (data) => {
      console.log('Backend:', data.toString());
    });

    backendProcess.stderr.on('data', (data) => {
      console.error('Backend Error:', data.toString());
    });

    backendProcess.on('close', (code) => {
      console.log('Backend process exited with code:', code);
      backendProcess = null;
    });

    console.log('Backend server started');
  } catch (error) {
    console.error('Failed to start backend server:', error);
    backendProcess = null;
  }
}

function createWindow() {
  // Start backend server first (only in production)
  if (!isDev) {
    startBackendServer();
  }

  // Wait a moment for backend to start in production
  const delay = isDev ? 0 : 3000;

  setTimeout(() => {
    // Create the browser window
    mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1200,
      minHeight: 800,
      frame: false, // Remove the window frame/title bar
      titleBarStyle: 'hidden', // Hide title bar on macOS
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, 'preload.js'),
        zoomFactor: 0.8 // Set default zoom to 80% (zoomed out)
      },
      icon: path.join(__dirname, '../assets/icon.png'), // Add icon later
      show: false
    });

    // Load the app
    const startUrl = isDev
      ? 'http://127.0.0.1:3000'
      : `file://${path.join(__dirname, '../build/index.html')}`;

    mainWindow.loadURL(startUrl);

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
      // Set zoom level programmatically (alternative method)
      // mainWindow.webContents.setZoomFactor(0.8);
      mainWindow.show();
    });

    // Open DevTools in development
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }

    // Handle window closed
    mainWindow.on('closed', () => {
      mainWindow = null;
    });
  }, delay);
}

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  // Kill backend process
  if (backendProcess) {
    console.log('Terminating backend process...');
    backendProcess.kill();
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers
ipcMain.handle('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window-close', () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.handle('window-is-maximized', () => {
  if (mainWindow) return mainWindow.isMaximized();
  return false;
});

ipcMain.handle('app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-notification', (event, title, body) => {
  const { Notification } = require('electron');
  if (Notification.isSupported()) {
    new Notification({ title, body }).show();
  }
});

ipcMain.handle('open-devtools', () => {
  if (mainWindow && isDev) {
    mainWindow.webContents.openDevTools();
  }
});

// WebSocket management
const WebSocket = require('ws');
let wsConnection = null;
let reconnectTimer = null;
let heartbeatTimer = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;
const heartbeatInterval = 30000; // 30 seconds

const connectWebSocket = (url) => {
  return new Promise((resolve, reject) => {
    try {
      if (wsConnection) {
        wsConnection.close();
      }

      wsConnection = new WebSocket(url);

      wsConnection.on('open', () => {
        console.log('WebSocket connected to:', url);
        reconnectAttempts = 0;

        // Start heartbeat
        startHeartbeat();

        // Send connection status to renderer
        if (mainWindow) {
          mainWindow.webContents.send('websocket-message', JSON.stringify({
            type: 'connection_status',
            connected: true,
            timestamp: new Date().toISOString()
          }));
        }

        resolve({ success: true, message: 'WebSocket connected successfully' });
      });

      wsConnection.on('message', (data) => {
        // Forward messages to renderer process
        if (mainWindow) {
          mainWindow.webContents.send('websocket-message', data.toString());
        }
      });

      wsConnection.on('close', (code, reason) => {
        console.log('WebSocket closed:', code, reason.toString());

        // Stop heartbeat
        stopHeartbeat();

        // Send disconnection status to renderer
        if (mainWindow) {
          mainWindow.webContents.send('websocket-message', JSON.stringify({
            type: 'connection_status',
            connected: false,
            timestamp: new Date().toISOString()
          }));
        }

        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);

          reconnectTimer = setTimeout(() => {
            reconnectAttempts++;
            connectWebSocket(url).catch(console.error);
          }, delay);
        }
      });

      wsConnection.on('error', (error) => {
        console.error('WebSocket error:', error);
        reject({ success: false, message: error.message });
      });

      // Connection timeout
      setTimeout(() => {
        if (wsConnection.readyState === WebSocket.CONNECTING) {
          wsConnection.close();
          reject({ success: false, message: 'Connection timeout' });
        }
      }, 10000);

    } catch (error) {
      reject({ success: false, message: error.message });
    }
  });
};

const startHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
  }

  heartbeatTimer = setInterval(() => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      const heartbeatMessage = {
        type: 'heartbeat',
        data: {
          client_time: Date.now(),
          client_id: 'electron_dashboard'
        }
      };

      try {
        wsConnection.send(JSON.stringify(heartbeatMessage));
        console.log('Heartbeat sent');
      } catch (error) {
        console.error('Failed to send heartbeat:', error);
      }
    }
  }, heartbeatInterval);
};

const stopHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
};

const disconnectWebSocket = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  stopHeartbeat();

  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }

  reconnectAttempts = 0;
  return { success: true, message: 'WebSocket disconnected' };
};

ipcMain.handle('websocket-connect', async (event, url) => {
  try {
    return await connectWebSocket(url);
  } catch (error) {
    return error;
  }
});

ipcMain.handle('websocket-disconnect', () => {
  return disconnectWebSocket();
});

// Send command to WebSocket server
ipcMain.handle('websocket-send', (event, data) => {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify(data));
    return { success: true, message: 'Message sent' };
  } else {
    return { success: false, message: 'WebSocket not connected' };
  }
});

// Create application menu
const template = [
  {
    label: 'File',
    submenu: [
      {
        label: 'Exit',
        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
        click: () => {
          app.quit();
        }
      }
    ]
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'forceReload' },
      { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'resetZoom' },
      { role: 'zoomIn' },
      { role: 'zoomOut' },
      { type: 'separator' },
      { role: 'togglefullscreen' }
    ]
  },
  {
    label: 'Window',
    submenu: [
      { role: 'minimize' },
      { role: 'close' }
    ]
  }
];

const menu = Menu.buildFromTemplate(template);
Menu.setApplicationMenu(menu);