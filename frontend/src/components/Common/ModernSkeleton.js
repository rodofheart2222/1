import React from 'react';
import { Skeleton } from 'antd';

const ModernSkeleton = ({ 
  type = 'card', 
  rows = 3, 
  avatar = false, 
  title = true,
  loading = true,
  children,
  className = ''
}) => {
  if (!loading) {
    return children;
  }

  const skeletonStyles = {
    background: 'linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 2s infinite',
    borderRadius: '8px'
  };

  const shimmerKeyframes = `
    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `;

  // Inject keyframes if not already present
  if (!document.querySelector('#shimmer-keyframes')) {
    const style = document.createElement('style');
    style.id = 'shimmer-keyframes';
    style.textContent = shimmerKeyframes;
    document.head.appendChild(style);
  }

  const renderCardSkeleton = () => (
    <div className={`modern-skeleton-card glass-card ${className}`} style={{ padding: '24px' }}>
      {title && (
        <div 
          style={{
            ...skeletonStyles,
            height: '24px',
            width: '60%',
            marginBottom: '16px'
          }}
        />
      )}
      {avatar && (
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
          <div 
            style={{
              ...skeletonStyles,
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              marginRight: '12px'
            }}
          />
          <div 
            style={{
              ...skeletonStyles,
              height: '16px',
              width: '120px'
            }}
          />
        </div>
      )}
      {Array.from({ length: rows }).map((_, index) => (
        <div 
          key={index}
          style={{
            ...skeletonStyles,
            height: '16px',
            width: index === rows - 1 ? '80%' : '100%',
            marginBottom: index === rows - 1 ? 0 : '12px'
          }}
        />
      ))}
    </div>
  );

  const renderStatsSkeleton = () => (
    <div className={`modern-skeleton-stats glass-card ${className}`} style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} style={{ textAlign: 'center', flex: 1 }}>
            <div 
              style={{
                ...skeletonStyles,
                height: '32px',
                width: '80px',
                margin: '0 auto 8px'
              }}
            />
            <div 
              style={{
                ...skeletonStyles,
                height: '14px',
                width: '60px',
                margin: '0 auto'
              }}
            />
          </div>
        ))}
      </div>
      <div 
        style={{
          ...skeletonStyles,
          height: '8px',
          width: '100%',
          borderRadius: '4px'
        }}
      />
    </div>
  );

  const renderGridSkeleton = () => (
    <div className={`modern-skeleton-grid ${className}`}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="glass-card" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
              <div 
                style={{
                  ...skeletonStyles,
                  width: '24px',
                  height: '24px',
                  borderRadius: '4px',
                  marginRight: '8px'
                }}
              />
              <div 
                style={{
                  ...skeletonStyles,
                  height: '18px',
                  width: '120px'
                }}
              />
            </div>
            {Array.from({ length: 3 }).map((_, rowIndex) => (
              <div 
                key={rowIndex}
                style={{
                  ...skeletonStyles,
                  height: '14px',
                  width: rowIndex === 2 ? '70%' : '100%',
                  marginBottom: rowIndex === 2 ? 0 : '8px'
                }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );

  const renderTableSkeleton = () => (
    <div className={`modern-skeleton-table glass-card ${className}`} style={{ padding: '24px' }}>
      {/* Table Header */}
      <div style={{ display: 'flex', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        {Array.from({ length: 5 }).map((_, index) => (
          <div 
            key={index}
            style={{
              ...skeletonStyles,
              height: '16px',
              width: '80px',
              flex: 1,
              marginRight: index === 4 ? 0 : '16px'
            }}
          />
        ))}
      </div>
      {/* Table Rows */}
      {Array.from({ length: 5 }).map((_, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex', marginBottom: '12px' }}>
          {Array.from({ length: 5 }).map((_, colIndex) => (
            <div 
              key={colIndex}
              style={{
                ...skeletonStyles,
                height: '14px',
                width: colIndex === 0 ? '60px' : '80px',
                flex: 1,
                marginRight: colIndex === 4 ? 0 : '16px'
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );

  switch (type) {
    case 'stats':
      return renderStatsSkeleton();
    case 'grid':
      return renderGridSkeleton();
    case 'table':
      return renderTableSkeleton();
    case 'card':
    default:
      return renderCardSkeleton();
  }
};

export default ModernSkeleton;