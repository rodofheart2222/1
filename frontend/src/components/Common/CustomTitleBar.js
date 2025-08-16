import React, { useState, useEffect } from 'react';
import { 
  MinusOutlined, 
  BorderOutlined, 
  CloseOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined
} from '@ant-design/icons';
import './CustomTitleBar.css';

const CustomTitleBar = () => {
  const [isMaximized, setIsMaximized] = useState(false);
  const [isElectron, setIsElectron] = useState(false);

  useEffect(() => {
    // Check if running in Electron
    setIsElectron(window.electronAPI !== undefined);
    
    // Check initial maximize state
    if (window.electronAPI) {
      window.electronAPI.isWindowMaximized().then(setIsMaximized);
    }
  }, []);

  const handleMinimize = () => {
    if (window.electronAPI) {
      window.electronAPI.minimizeWindow();
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI) {
      window.electronAPI.maximizeWindow();
      setIsMaximized(!isMaximized);
    }
  };

  const handleClose = () => {
    if (window.electronAPI) {
      window.electronAPI.closeWindow();
    }
  };

  // Don't render if not in Electron
  if (!isElectron) {
    return null;
  }

  return (
    <div className="custom-title-bar">
      <div className="title-bar-drag-region">
        <div className="title-bar-title">
          <span className="app-name">NEXUS COMMAND</span>
          <span className="app-subtitle">Trading Intelligence</span>
        </div>
      </div>
      
      <div className="title-bar-controls">
        <button 
          className="title-bar-button minimize-button"
          onClick={handleMinimize}
          title="Minimize"
        >
          <MinusOutlined />
        </button>
        
        <button 
          className="title-bar-button maximize-button"
          onClick={handleMaximize}
          title={isMaximized ? "Restore" : "Maximize"}
        >
          {isMaximized ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
        </button>
        
        <button 
          className="title-bar-button close-button"
          onClick={handleClose}
          title="Close"
        >
          <CloseOutlined />
        </button>
      </div>
    </div>
  );
};

export default CustomTitleBar;