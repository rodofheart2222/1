import React, { createContext, useContext, useReducer, useEffect } from 'react';

// Initial state
const initialState = {
  // Connection state
  connected: false,
  connecting: false,
  connectionError: null,
  
  // EA data
  eaData: [],
  eaDataLoading: false,
  eaDataError: null,
  
  // Global statistics
  globalStats: {
    totalPnL: 0,
    totalDrawdown: 0,
    winRate: 0,
    totalTrades: 0,
    activeEAs: 0,
    totalEAs: 0,
    dailyPnL: 0,
    weeklyPnL: 0
  },
  globalStatsLoading: false,
  globalStatsError: null,
  
  // News events
  newsEvents: [],
  newsEventsLoading: false,
  newsEventsError: null,
  
  // Commands
  commandQueue: [],
  commandHistory: [],
  commandLoading: false,
  commandError: null,
  
  // UI state
  selectedEAs: [],
  filters: {
    symbol: 'all',
    strategy: 'all',
    status: 'all',
    riskLevel: 'all',
    search: '',
    profitRange: [-1000, 1000],
    drawdownMax: 100
  },
  
  // Settings
  settings: {
    autoReconnect: true,
    refreshInterval: 1000,
    maxReconnectAttempts: 10,
    theme: 'light'
  }
};

// Action types
const ActionTypes = {
  // Connection actions
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS',
  SET_CONNECTING: 'SET_CONNECTING',
  SET_CONNECTION_ERROR: 'SET_CONNECTION_ERROR',
  
  // EA data actions
  SET_EA_DATA: 'SET_EA_DATA',
  UPDATE_EA_DATA: 'UPDATE_EA_DATA',
  SET_EA_DATA_LOADING: 'SET_EA_DATA_LOADING',
  SET_EA_DATA_ERROR: 'SET_EA_DATA_ERROR',
  
  // Global stats actions
  SET_GLOBAL_STATS: 'SET_GLOBAL_STATS',
  SET_GLOBAL_STATS_LOADING: 'SET_GLOBAL_STATS_LOADING',
  SET_GLOBAL_STATS_ERROR: 'SET_GLOBAL_STATS_ERROR',
  
  // News events actions
  SET_NEWS_EVENTS: 'SET_NEWS_EVENTS',
  SET_NEWS_EVENTS_LOADING: 'SET_NEWS_EVENTS_LOADING',
  SET_NEWS_EVENTS_ERROR: 'SET_NEWS_EVENTS_ERROR',
  
  // Command actions
  ADD_COMMAND: 'ADD_COMMAND',
  UPDATE_COMMAND: 'UPDATE_COMMAND',
  SET_COMMAND_LOADING: 'SET_COMMAND_LOADING',
  SET_COMMAND_ERROR: 'SET_COMMAND_ERROR',
  CLEAR_COMMAND_QUEUE: 'CLEAR_COMMAND_QUEUE',
  
  // UI actions
  SET_SELECTED_EAS: 'SET_SELECTED_EAS',
  SET_FILTERS: 'SET_FILTERS',
  UPDATE_FILTER: 'UPDATE_FILTER',
  
  // Settings actions
  UPDATE_SETTINGS: 'UPDATE_SETTINGS',
  
  // Reset actions
  RESET_STATE: 'RESET_STATE'
};

// Reducer function
const dashboardReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_CONNECTION_STATUS:
      return {
        ...state,
        connected: action.payload,
        connecting: false,
        connectionError: action.payload ? null : state.connectionError
      };
      
    case ActionTypes.SET_CONNECTING:
      return {
        ...state,
        connecting: action.payload,
        connectionError: action.payload ? null : state.connectionError
      };
      
    case ActionTypes.SET_CONNECTION_ERROR:
      return {
        ...state,
        connectionError: action.payload,
        connecting: false,
        connected: false
      };
      
    case ActionTypes.SET_EA_DATA:
      return {
        ...state,
        eaData: action.payload,
        eaDataLoading: false,
        eaDataError: null
      };
      
    case ActionTypes.UPDATE_EA_DATA:
      const updatedEAData = [...state.eaData];
      const existingIndex = updatedEAData.findIndex(
        ea => ea.magic_number === action.payload.magic_number
      );
      
      if (existingIndex >= 0) {
        updatedEAData[existingIndex] = { ...updatedEAData[existingIndex], ...action.payload };
      } else {
        updatedEAData.push(action.payload);
      }
      
      return {
        ...state,
        eaData: updatedEAData,
        eaDataError: null
      };
      
    case ActionTypes.SET_EA_DATA_LOADING:
      return {
        ...state,
        eaDataLoading: action.payload
      };
      
    case ActionTypes.SET_EA_DATA_ERROR:
      return {
        ...state,
        eaDataError: action.payload,
        eaDataLoading: false
      };
      
    case ActionTypes.SET_GLOBAL_STATS:
      return {
        ...state,
        globalStats: { ...state.globalStats, ...action.payload },
        globalStatsLoading: false,
        globalStatsError: null
      };
      
    case ActionTypes.SET_GLOBAL_STATS_LOADING:
      return {
        ...state,
        globalStatsLoading: action.payload
      };
      
    case ActionTypes.SET_GLOBAL_STATS_ERROR:
      return {
        ...state,
        globalStatsError: action.payload,
        globalStatsLoading: false
      };
      
    case ActionTypes.SET_NEWS_EVENTS:
      return {
        ...state,
        newsEvents: action.payload,
        newsEventsLoading: false,
        newsEventsError: null
      };
      
    case ActionTypes.SET_NEWS_EVENTS_LOADING:
      return {
        ...state,
        newsEventsLoading: action.payload
      };
      
    case ActionTypes.SET_NEWS_EVENTS_ERROR:
      return {
        ...state,
        newsEventsError: action.payload,
        newsEventsLoading: false
      };
      
    case ActionTypes.ADD_COMMAND:
      return {
        ...state,
        commandQueue: [...state.commandQueue, action.payload],
        commandError: null
      };
      
    case ActionTypes.UPDATE_COMMAND:
      const updatedQueue = state.commandQueue.map(cmd =>
        cmd.id === action.payload.id ? { ...cmd, ...action.payload } : cmd
      );
      
      return {
        ...state,
        commandQueue: updatedQueue,
        commandHistory: action.payload.status === 'completed' 
          ? [...state.commandHistory, action.payload]
          : state.commandHistory
      };
      
    case ActionTypes.SET_COMMAND_LOADING:
      return {
        ...state,
        commandLoading: action.payload
      };
      
    case ActionTypes.SET_COMMAND_ERROR:
      return {
        ...state,
        commandError: action.payload,
        commandLoading: false
      };
      
    case ActionTypes.CLEAR_COMMAND_QUEUE:
      return {
        ...state,
        commandQueue: []
      };
      
    case ActionTypes.SET_SELECTED_EAS:
      return {
        ...state,
        selectedEAs: action.payload
      };
      
    case ActionTypes.SET_FILTERS:
      return {
        ...state,
        filters: { ...state.filters, ...action.payload }
      };
      
    case ActionTypes.UPDATE_FILTER:
      return {
        ...state,
        filters: {
          ...state.filters,
          [action.payload.key]: action.payload.value
        }
      };
      
    case ActionTypes.UPDATE_SETTINGS:
      return {
        ...state,
        settings: { ...state.settings, ...action.payload }
      };
      
    case ActionTypes.RESET_STATE:
      return {
        ...initialState,
        settings: state.settings // Preserve settings
      };
      
    default:
      return state;
  }
};

// Create context
const DashboardContext = createContext();

// Context provider component
export const DashboardProvider = ({ children }) => {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);

  // Action creators
  const actions = {
    // Connection actions
    setConnectionStatus: (connected) => 
      dispatch({ type: ActionTypes.SET_CONNECTION_STATUS, payload: connected }),
    
    setConnecting: (connecting) => 
      dispatch({ type: ActionTypes.SET_CONNECTING, payload: connecting }),
    
    setConnectionError: (error) => 
      dispatch({ type: ActionTypes.SET_CONNECTION_ERROR, payload: error }),
    
    // EA data actions
    setEAData: (data) => 
      dispatch({ type: ActionTypes.SET_EA_DATA, payload: data }),
    
    updateEAData: (eaData) => 
      dispatch({ type: ActionTypes.UPDATE_EA_DATA, payload: eaData }),
    
    setEADataLoading: (loading) => 
      dispatch({ type: ActionTypes.SET_EA_DATA_LOADING, payload: loading }),
    
    setEADataError: (error) => 
      dispatch({ type: ActionTypes.SET_EA_DATA_ERROR, payload: error }),
    
    // Global stats actions
    setGlobalStats: (stats) => 
      dispatch({ type: ActionTypes.SET_GLOBAL_STATS, payload: stats }),
    
    setGlobalStatsLoading: (loading) => 
      dispatch({ type: ActionTypes.SET_GLOBAL_STATS_LOADING, payload: loading }),
    
    setGlobalStatsError: (error) => 
      dispatch({ type: ActionTypes.SET_GLOBAL_STATS_ERROR, payload: error }),
    
    // News events actions
    setNewsEvents: (events) => 
      dispatch({ type: ActionTypes.SET_NEWS_EVENTS, payload: events }),
    
    setNewsEventsLoading: (loading) => 
      dispatch({ type: ActionTypes.SET_NEWS_EVENTS_LOADING, payload: loading }),
    
    setNewsEventsError: (error) => 
      dispatch({ type: ActionTypes.SET_NEWS_EVENTS_ERROR, payload: error }),
    
    // Command actions
    addCommand: (command) => 
      dispatch({ type: ActionTypes.ADD_COMMAND, payload: { ...command, id: Date.now() } }),
    
    updateCommand: (command) => 
      dispatch({ type: ActionTypes.UPDATE_COMMAND, payload: command }),
    
    setCommandLoading: (loading) => 
      dispatch({ type: ActionTypes.SET_COMMAND_LOADING, payload: loading }),
    
    setCommandError: (error) => 
      dispatch({ type: ActionTypes.SET_COMMAND_ERROR, payload: error }),
    
    clearCommandQueue: () => 
      dispatch({ type: ActionTypes.CLEAR_COMMAND_QUEUE }),
    
    // UI actions
    setSelectedEAs: (eas) => 
      dispatch({ type: ActionTypes.SET_SELECTED_EAS, payload: eas }),
    
    setFilters: (filters) => 
      dispatch({ type: ActionTypes.SET_FILTERS, payload: filters }),
    
    updateFilter: (key, value) => 
      dispatch({ type: ActionTypes.UPDATE_FILTER, payload: { key, value } }),
    
    // Settings actions
    updateSettings: (settings) => 
      dispatch({ type: ActionTypes.UPDATE_SETTINGS, payload: settings }),
    
    // Reset actions
    resetState: () => 
      dispatch({ type: ActionTypes.RESET_STATE })
  };

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('dashboard-settings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        actions.updateSettings(settings);
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    }
  }, []);

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('dashboard-settings', JSON.stringify(state.settings));
  }, [state.settings]);

  const value = {
    state,
    actions,
    ActionTypes
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

// Custom hook to use the dashboard context
export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};

export default DashboardContext;