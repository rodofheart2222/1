import { useState, useEffect, useRef } from 'react';

const SmoothTicker = ({
  targetValue,
  decimals = 5,
  prefix = '',
  suffix = '',
  className = '',
  style = {},
  showChangeIndicator = true
}) => {
  const [currentValue, setCurrentValue] = useState(targetValue || 0);
  const [animationClass, setAnimationClass] = useState('');
  const previousTargetRef = useRef(targetValue || 0);

  useEffect(() => {
    // Skip if no change or invalid values
    if (targetValue === previousTargetRef.current ||
      typeof targetValue !== 'number' ||
      isNaN(targetValue)) {
      return;
    }

    const previousTarget = previousTargetRef.current;
    const difference = Math.abs(targetValue - previousTarget);

    // Skip very small changes to avoid unnecessary animations
    if (difference < 0.00001) return;

    const isIncrease = targetValue > previousTarget;
    const isDecrease = targetValue < previousTarget;

    // Set animation class for flash effect
    if (showChangeIndicator) {
      if (isIncrease) {
        setAnimationClass('price-up');
      } else if (isDecrease) {
        setAnimationClass('price-down');
      }

      // Remove animation class after flash
      setTimeout(() => {
        setAnimationClass('');
      }, 300);
    }

    // Instant update like real market tickers
    setCurrentValue(targetValue);
    previousTargetRef.current = targetValue;

  }, [targetValue, showChangeIndicator]);

  // No cleanup needed for instant updates

  const formatValue = (val) => {
    if (typeof val !== 'number' || isNaN(val)) return '0';
    return val.toFixed(decimals);
  };

  return (
    <span
      className={`price-value smooth-ticker water-flow ${animationClass} ${className}`}
      style={style}
    >
      {prefix}{formatValue(currentValue)}{suffix}
    </span>
  );
};

export default SmoothTicker;