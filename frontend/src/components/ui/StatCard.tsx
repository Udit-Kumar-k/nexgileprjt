import React from 'react';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  subtitle?: string;
  variant?: 'default' | 'emerald' | 'amber' | 'blue';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  change,
  changeLabel = 'vs baseline',
  icon,
  subtitle,
  variant = 'default',
}) => {
  const borderColors = {
    default: 'hover:border-slate-700/80',
    emerald: 'hover:border-emerald-500/50',
    amber: 'hover:border-amber-500/50',
    blue: 'hover:border-sky-500/50',
  };

  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;

  return (
    <div className={`glass-panel p-5 rounded-xl transition-all duration-200 ${borderColors[variant]} relative overflow-hidden group`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-slate-800/80 flex items-center justify-center text-slate-300 group-hover:text-emerald-400 transition-colors">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {unit && <span className="text-xs font-medium text-slate-400">{unit}</span>}
      </div>

      {(change !== undefined || subtitle) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {change !== undefined && (
            <span
              className={`flex items-center gap-0.5 font-medium px-1.5 py-0.5 rounded ${
                isNegative
                  ? 'text-emerald-400 bg-emerald-950/60'
                  : isPositive
                  ? 'text-rose-400 bg-rose-950/60'
                  : 'text-slate-400 bg-slate-800'
              }`}
            >
              {isNegative && <TrendingDown className="w-3.5 h-3.5" />}
              {isPositive && <TrendingUp className="w-3.5 h-3.5" />}
              {change === 0 && <Minus className="w-3.5 h-3.5" />}
              {Math.abs(change)}%
            </span>
          )}
          <span className="text-slate-400 truncate">{subtitle || changeLabel}</span>
        </div>
      )}
    </div>
  );
};
