import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'scope1' | 'scope2' | 'scope3' | 'success' | 'warning' | 'danger' | 'neutral' | 'info';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', size = 'sm' }) => {
  const variantStyles = {
    scope1: 'bg-amber-950/60 text-amber-300 border-amber-800/50',
    scope2: 'bg-sky-950/60 text-sky-300 border-sky-800/50',
    scope3: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50',
    success: 'bg-emerald-950/60 text-emerald-400 border-emerald-700/50',
    warning: 'bg-amber-950/60 text-amber-400 border-amber-700/50',
    danger: 'bg-rose-950/60 text-rose-400 border-rose-700/50',
    neutral: 'bg-slate-800/80 text-slate-300 border-slate-700/50',
    info: 'bg-indigo-950/60 text-indigo-300 border-indigo-800/50',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-medium',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border ${variantStyles[variant]} ${sizeStyles[size]} tracking-wide`}
    >
      {children}
    </span>
  );
};
