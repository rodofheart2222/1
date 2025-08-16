# MT5 COC Dashboard - Electron Frontend

This is the Electron-based frontend application for the MT5 Commander-in-Chief + Soldier EA Dashboard System.

## Architecture

The application is built using:
- **Electron**: Desktop application framework
- **React**: Frontend UI library
- **Ant Design**: UI component library
- **Context API**: State management
- **WebSocket**: Real-time communication with backend

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.js          # Main dashboard container
│   │   │   ├── GlobalStatsPanel.js   # Portfolio statistics
│   │   │   ├── EAGridView.js         # EA grid with filtering
│   │   │   ├── SoldierEAPanel.js     # Individual EA panel
│   │   │   ├── NewsEventPanel.js     # News events display
│   │   │   ├── CommandCenter.js      # Command execution interface
│   │   │   └── Dashboard.css         # Dashboard styles
│   │   └── Common/
│   │       └── ConnectionStatus.js   # WebSocket connection indicator
│   ├── context/
│   │   └── DashboardContext.js       # Global state management
│   ├── test/
│   │   └── ElectronApp.test.js       # Integration tests
│   ├── App.js                        # Main app component
│   ├── App.css                       # Global styles
│   ├── index.js                      # React entry point
│   ├── main.js                       # Electron main process
│   └── preload.js                    # Electron preload script
├── public/
│   └── index.html                    # HTML template
├── package.json                      # Dependencies and scripts
└── README.md                         # This file
```

## Features Implemented

### 1. Electron Main Process
-  Secure window creation with context isolation
-  IPC communication handlers
-  WebSocket client integration
-  Auto-reconnection with exponential backoff
-  Application menu setup

### 2. React Frontend Structure
-  Component-based architecture
-  Responsive layout system
-  Dashboard with multiple panels
-  EA grid view with filtering
-  Global statistics panel
-  News events panel
-  Command center interface

### 3. WebSocket Client
-  Real-time data reception
-  Automatic reconnection
-  Message routing to components
-  Connection status monitoring

### 4. Responsive Layout Framework
-  Mobile-first responsive design
-  Flexible grid system
-  Adaptive component sizing
-  Print-friendly styles

### 5. State Management
-  React Context-based state management
-  Centralized action dispatching
-  Persistent settings storage
-  Real-time data updates

## Development Scripts

```bash
# Install dependencies
npm install

# Start development server (React only)
npm run dev:react

# Start Electron in development mode
npm run dev

# Build React app for production
npm run build

# Build Electron app for distribution
npm run build:electron

# Run tests
npm test
```

## WebSocket Communication

The frontend connects to the Python backend via WebSocket on `ws://155.138.174.196:8765`.

### Message Types Handled:
- `ea_update`: Individual EA status updates
- `portfolio_update`: Global portfolio statistics
- `news_update`: News events data
- `connection_status`: Backend connection status

### Message Format:
```json
{
  "type": "ea_update",
  "data": {
    "magic_number": 12345,
    "symbol": "EURUSD",
    "current_profit": 150.25,
    // ... other EA data
  },
  "timestamp": "2024-12-08T10:30:00Z"
}
```

## State Management

The application uses React Context for state management with the following structure:

### State Structure:
```javascript
{
  // Connection state
  connected: boolean,
  connecting: boolean,
  connectionError: string,
  
  // EA data
  eaData: Array<EAData>,
  eaDataLoading: boolean,
  eaDataError: string,
  
  // Global statistics
  globalStats: GlobalStats,
  
  // News events
  newsEvents: Array<NewsEvent>,
  
  // Commands
  commandQueue: Array<Command>,
  commandHistory: Array<Command>,
  
  // UI state
  selectedEAs: Array<string>,
  filters: FilterState,
  
  // Settings
  settings: AppSettings
}
```

### Available Actions:
- Connection management: `setConnectionStatus`, `setConnecting`, `setConnectionError`
- EA data: `setEAData`, `updateEAData`, `setEADataLoading`, `setEADataError`
- Global stats: `setGlobalStats`, `setGlobalStatsLoading`, `setGlobalStatsError`
- News events: `setNewsEvents`, `setNewsEventsLoading`, `setNewsEventsError`
- Commands: `addCommand`, `updateCommand`, `setCommandLoading`, `setCommandError`
- UI: `setSelectedEAs`, `setFilters`, `updateFilter`
- Settings: `updateSettings`

## Security Features

- Context isolation enabled
- Node integration disabled in renderer
- Secure IPC communication via preload script
- No direct access to Node.js APIs from renderer

## Responsive Design

The application is designed to work on various screen sizes:
- **Desktop**: Full dashboard with all panels
- **Tablet**: Stacked layout with collapsible panels
- **Mobile**: Single-column layout with simplified UI

### Breakpoints:
- Desktop: > 1200px
- Tablet: 768px - 1200px
- Mobile: < 768px

## Testing

The application includes integration tests for:
- Component rendering
- Context provider functionality
- Responsive layout
- WebSocket communication (mocked)

Run tests with:
```bash
npm test
```

## Production Build

To create a production build:

1. Build React app: `npm run build`
2. Build Electron app: `npm run build:electron`

The built application will be in the `dist/` directory.

## Configuration

### Electron Configuration
- Window size: 1400x900 (minimum 1200x800)
- Security: Context isolation enabled
- DevTools: Available in development mode

### WebSocket Configuration
- Default URL: `ws://155.138.174.196:8765`
- Auto-reconnect: Enabled with exponential backoff
- Max reconnect attempts: 10

## Next Steps

This foundation provides:
1.  Complete Electron application setup
2.  React component structure
3.  WebSocket client implementation
4.  Responsive layout framework
5.  State management system

The application is ready for integration with the backend WebSocket server and can display real-time EA data, portfolio statistics, news events, and handle command execution.