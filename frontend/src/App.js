import React, { useEffect, useRef, useState } from 'react';
import { Layout, ConfigProvider, theme as antdTheme } from 'antd';
import { DashboardProvider, useDashboard } from './context/DashboardContext';
import { NotificationProvider } from './components/Common/NotificationSystem';
import CustomTitleBar from './components/Common/CustomTitleBar';
import TickerBar from './components/Common/TickerBar';
import Dashboard from './components/Dashboard/Dashboard';
import { initializeTheme } from './config/theme-config';
import './App.css';
import './theme.css';

const { Header, Footer } = Layout;

// Modern Black Theme Configuration
const theme = {
  token: {
    // Primary colors
    colorPrimary: '#00d4ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',

    // Background colors
    colorBgBase: '#0a0a0a',
    colorBgContainer: '#141414',
    colorBgElevated: '#1f1f1f',
    colorBgLayout: '#000000',
    colorBgSpotlight: '#262626',

    // Text colors
    colorText: '#ffffff',
    colorTextSecondary: '#a6a6a6',
    colorTextTertiary: '#737373',
    colorTextQuaternary: '#595959',

    // Border colors
    colorBorder: '#303030',
    colorBorderSecondary: '#262626',

    // Component styling
    borderRadius: 8,
    fontSize: 14,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',

    // Shadows
    boxShadow: '0 6px 16px 0 rgba(0, 0, 0, 0.8), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
    boxShadowSecondary: '0 6px 16px 0 rgba(0, 0, 0, 0.8)',
  },
  components: {
    Layout: {
      headerBg: '#000000',
      headerHeight: 56,
      bodyBg: '#0a0a0a',
      footerBg: '#141414',
      siderBg: '#141414',
    },
    Card: {
      headerBg: '#1f1f1f',
      colorBgContainer: '#141414',
      colorBorderSecondary: '#303030',
    },
    Button: {
      colorBgContainer: '#262626',
      colorBorder: '#404040',
      colorText: '#ffffff',
    },
    Input: {
      colorBgContainer: '#262626',
      colorBorder: '#404040',
      colorText: '#ffffff',
      colorTextPlaceholder: '#8c8c8c',
    },
    Select: {
      colorBgContainer: '#262626',
      colorBgElevated: '#1f1f1f',
      colorBorder: '#404040',
      colorText: '#ffffff',
    },
    Table: {
      colorBgContainer: '#141414',
      headerBg: '#1f1f1f',
      headerColor: '#ffffff',
      colorText: '#ffffff',
      colorBorder: '#303030',
      rowHoverBg: '#262626',
    },
    Menu: {
      colorBgContainer: '#141414',
      colorItemBg: '#141414',
      colorItemText: '#ffffff',
      colorItemTextSelected: '#00d4ff',
      colorActiveBarBorderSize: 0,
    },
    Statistic: {
      colorText: '#ffffff',
      colorTextDescription: '#a6a6a6',
    },
    Alert: {
      colorInfoBg: '#111b26',
      colorInfoBorder: '#153450',
      colorSuccessBg: '#162312',
      colorSuccessBorder: '#274916',
      colorWarningBg: '#2b2111',
      colorWarningBorder: '#594214',
      colorErrorBg: '#2a1215',
      colorErrorBorder: '#58181c',
    },
    Collapse: {
      colorBgContainer: '#141414',
      headerBg: '#1f1f1f',
      colorBorder: '#303030',
      colorText: '#ffffff',
    },
    Switch: {
      colorPrimary: '#00d4ff',
      colorPrimaryHover: '#40e0ff',
    },
    Progress: {
      colorSuccess: '#52c41a',
      colorException: '#ff4d4f',
    },
    Spin: {
      colorPrimary: '#00d4ff',
    },
    Tooltip: {
      colorBgSpotlight: '#262626',
      colorTextLightSolid: '#ffffff',
    },
    Drawer: {
      colorBgElevated: '#1f1f1f',
      colorBgMask: 'rgba(0, 0, 0, 0.45)',
    },
    Modal: {
      contentBg: '#1f1f1f',
      headerBg: '#1f1f1f',
      colorText: '#ffffff',
    },
    Tabs: {
      colorBgContainer: '#141414',
      colorText: '#ffffff',
      colorPrimary: '#00d4ff',
    },
    List: {
      colorBgContainer: '#141414',
      colorText: '#ffffff',
      colorBorder: '#303030',
    },
  },
  algorithm: 'darkAlgorithm',
};

// Inner component that has access to dashboard context
const AppContent = () => {
  const { state } = useDashboard();
  const { connected, eaData, newsEvents } = state;
  
  // Manage dashboard mode at the app level
  const [dashboardMode, setDashboardMode] = useState('soldier');
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleModeSwitch = (newMode) => {
    if (newMode === dashboardMode || isTransitioning) return;
    
    setIsTransitioning(true);
    setDashboardMode(newMode);
    
    // Reset transitioning state after animation completes
    setTimeout(() => {
      setIsTransitioning(false);
    }, 600);
  };

  return (
    <>
      <CustomTitleBar />
      <TickerBar 
        connected={connected}
        eaData={eaData}
        dashboardMode={dashboardMode}
        isTransitioning={isTransitioning}
        onModeSwitch={handleModeSwitch}
        newsEvents={newsEvents || []}
      />
      <Layout className="app-layout" style={{ marginTop: '60px' }}> {/* Account for ticker bar (28px) + advanced intelligence header (32px) */}
        <Dashboard 
          dashboardMode={dashboardMode}
          isTransitioning={isTransitioning}
        />

        <Footer className="app-footer">
          <span className="footer-text">
            MT5 COC Dashboard ©2025 - Real-time Trading Management System
          </span>
        </Footer>
      </Layout>
    </>
  );
};

function App() {
  const commanderRef = useRef(null);

  // Initialize liquid glass theme
  useEffect(() => {
    initializeTheme();
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const commanderElement = commanderRef.current;

      if (commanderElement) {
        if (scrollY > 50) {
          // Slide in when scrolled down
          commanderElement.classList.add('slide-in');
          commanderElement.classList.remove('slide-out');
        } else {
          // Slide out when at top
          commanderElement.classList.add('slide-out');
          commanderElement.classList.remove('slide-in');
        }
      }
    };

    // Initial state - hidden at top
    if (commanderRef.current) {
      commanderRef.current.classList.add('slide-out');
    }

    // Add scroll event listener
    window.addEventListener('scroll', handleScroll);

    // Cleanup
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <ConfigProvider
      theme={{
        ...theme,
        algorithm: antdTheme.darkAlgorithm,
      }}
    >
      <NotificationProvider>
        <DashboardProvider>
          <AppContent />
        </DashboardProvider>
      </NotificationProvider>
    </ConfigProvider>
  );
}

export default App;