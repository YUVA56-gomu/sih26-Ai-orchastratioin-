import React from 'react';

interface LogoProps {
  variant?: 'blue' | 'white' | 'black' | 'wordmark';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'h-6 w-6',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
  xl: 'h-20 w-20',
};

export const Logo: React.FC<LogoProps> = ({
  variant = 'blue',
  size = 'md',
  showText = true,
  className = '',
}) => {
  if (variant === 'wordmark') {
    return (
      <img
        src="/assets/logo-wordmark.jpg"
        alt="SAMUDRA AI Logo"
        className={`object-contain rounded-lg shadow-lg ${className}`}
      />
    );
  }

  const src =
    variant === 'white'
      ? '/assets/logo-white.png'
      : variant === 'black'
      ? '/assets/logo-black.png'
      : '/assets/logo-blue.png';

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <img
        src={src}
        alt="SAMUDRA AI Icon"
        className={`${sizeClasses[size]} object-contain filter drop-shadow-sm transition-transform hover:scale-105`}
      />
      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-bold tracking-tight text-white font-sans text-lg">
              SAMUDRA
            </span>
            <span className="font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent text-lg">
              AI
            </span>
          </div>
          <span className="text-[10px] tracking-widest text-slate-400 uppercase font-semibold -mt-1">
            Marine Intelligence
          </span>
        </div>
      )}
    </div>
  );
};
