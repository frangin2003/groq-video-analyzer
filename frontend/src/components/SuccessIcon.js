import React, { useState, useEffect } from 'react';

const SuccessIcon = () => {
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsAnimating(false);
    }, 600);
    return () => clearTimeout(timer);
  }, []);

  return (
    <svg 
      className="w-16 h-16 mx-auto"
      viewBox="0 0 24 24"
    >
      <path 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        strokeWidth={2}
        d="M5 13l4 4L19 7"
        stroke="rgb(147, 51, 234)"
        fill="none"
        style={{
          strokeDasharray: 30,
          strokeDashoffset: isAnimating ? 30 : 0,
          transition: 'stroke-dashoffset 0.6s ease-out'
        }}
      />
    </svg>
  );
};

export default SuccessIcon;