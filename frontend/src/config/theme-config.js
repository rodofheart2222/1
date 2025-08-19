/**
 * Centralized Theme Configuration
 * Manages liquid glass theme variables and provides theme switching functionality
 */

// Theme Modes
export const THEME_MODES = {
  LIGHT: 'light',
  DARK: 'dark',
  DIM: 'dim'
};

// Default Theme Variables
export const DEFAULT_THEME_VARS = {
  // Base Colors
  glass: '#bbbbbc',
  light: '#fff',
  dark: '#000',
  
  // Content Colors
  content: '#224',
  action: '#0052f5',
  
  // Background
  bg: '#E8E8E9',
  
  // Glass Reflex Intensities
  glassReflexDark: 1,
  glassReflexLight: 1,
  
  // Saturation
  saturation: '150%',
  
  // Transitions
  transition: '400ms cubic-bezier(1, 0.0, 0.4, 1)',
  transitionFast: '160ms cubic-bezier(0.5, 0, 0, 1)'
};

// Theme Variants
export const THEME_VARIANTS = {
  [THEME_MODES.LIGHT]: {
    ...DEFAULT_THEME_VARS,
    // Light theme is the default
  },
  
  [THEME_MODES.DARK]: {
    ...DEFAULT_THEME_VARS,
    content: '#e1e1e1',
    action: '#03d5ff',
    bg: '#1b1b1d',
    glassReflexDark: 2,
    glassReflexLight: 0.3,
    saturation: '150%'
  },
  
  [THEME_MODES.DIM]: {
    ...DEFAULT_THEME_VARS,
    light: '#99deff',
    dark: '#20001b',
    glass: 'hsl(335 250% 74% / 1)',
    content: '#d5dbe2',
    action: '#ff48a9',
    bg: '#152433',
    glassReflexDark: 2,
    glassReflexLight: 0.7,
    saturation: '200%'
  }
};

/**
 * Apply theme variables to CSS custom properties
 * @param {string} theme - Theme mode (light, dark, dim)
 */
export const applyTheme = (theme = THEME_MODES.LIGHT) => {
  const themeVars = THEME_VARIANTS[theme] || THEME_VARIANTS[THEME_MODES.LIGHT];
  const root = document.documentElement;
  
  // Apply CSS custom properties
  root.style.setProperty('--lg-glass', themeVars.glass);
  root.style.setProperty('--lg-light', themeVars.light);
  root.style.setProperty('--lg-dark', themeVars.dark);
  root.style.setProperty('--lg-content', themeVars.content);
  root.style.setProperty('--lg-action', themeVars.action);
  root.style.setProperty('--lg-bg', themeVars.bg);
  root.style.setProperty('--lg-glass-reflex-dark', themeVars.glassReflexDark);
  root.style.setProperty('--lg-glass-reflex-light', themeVars.glassReflexLight);
  root.style.setProperty('--lg-saturation', themeVars.saturation);
  root.style.setProperty('--lg-transition', themeVars.transition);
  root.style.setProperty('--lg-transition-fast', themeVars.transitionFast);
  
  // Set theme attribute on body for theme-specific styles
  document.body.setAttribute('data-theme', theme);
  
  // Store current theme in localStorage
  localStorage.setItem('liquid-glass-theme', theme);
};

/**
 * Get current theme from localStorage or default
 * @returns {string} Current theme mode
 */
export const getCurrentTheme = () => {
  return localStorage.getItem('liquid-glass-theme') || THEME_MODES.LIGHT;
};

/**
 * Initialize theme on app startup
 */
export const initializeTheme = () => {
  const savedTheme = getCurrentTheme();
  applyTheme(savedTheme);
};

/**
 * Create theme switcher component data
 * @returns {Array} Theme options for switcher component
 */
export const getThemeSwitcherOptions = () => [
  {
    value: THEME_MODES.LIGHT,
    label: 'Light',
    icon: '☀️',
    description: 'Clean light theme with subtle glass effects'
  },
  {
    value: THEME_MODES.DARK,
    label: 'Dark',
    icon: '🌙',
    description: 'Dark theme with enhanced glass reflections'
  },
  {
    value: THEME_MODES.DIM,
    label: 'Dim',
    icon: '🌆',
    description: 'Atmospheric dim theme with colored glass'
  }
];

/**
 * Theme utility functions
 */
export const themeUtils = {
  /**
   * Check if current theme is dark
   * @returns {boolean} True if dark or dim theme
   */
  isDark: () => {
    const theme = getCurrentTheme();
    return theme === THEME_MODES.DARK || theme === THEME_MODES.DIM;
  },
  
  /**
   * Get theme-appropriate text color
   * @param {string} theme - Theme mode
   * @returns {string} Text color
   */
  getTextColor: (theme = getCurrentTheme()) => {
    const themeVars = THEME_VARIANTS[theme];
    return themeVars.content;
  },
  
  /**
   * Get theme-appropriate action color
   * @param {string} theme - Theme mode
   * @returns {string} Action color
   */
  getActionColor: (theme = getCurrentTheme()) => {
    const themeVars = THEME_VARIANTS[theme];
    return themeVars.action;
  },
  
  /**
   * Generate glass effect background
   * @param {number} opacity - Glass opacity (0-1)
   * @param {string} theme - Theme mode
   * @returns {string} CSS background value
   */
  getGlassBackground: (opacity = 0.12, theme = getCurrentTheme()) => {
    const themeVars = THEME_VARIANTS[theme];
    return `color-mix(in srgb, ${themeVars.glass} ${opacity * 100}%, transparent)`;
  }
};

export default {
  THEME_MODES,
  DEFAULT_THEME_VARS,
  THEME_VARIANTS,
  applyTheme,
  getCurrentTheme,
  initializeTheme,
  getThemeSwitcherOptions,
  themeUtils
};
