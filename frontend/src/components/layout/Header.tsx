import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, Calendar, UserCheck, LogOut, ChevronDown } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useFilterStore } from '../../store/filterStore';
import { UserRole } from '../../types';

export const Header: React.FC = () => {
  const { user, logout, switchRole } = useAuthStore();
  const { reportingYear, setReportingYear } = useFilterStore();
  const navigate = useNavigate();

  const handleRoleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const role = e.target.value as UserRole;
    await switchRole(role);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Organization & Reporting Year */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Globe className="w-4 h-4 text-emerald-400" />
          <span>Nexgile Global Technologies Inc.</span>
        </div>

        <div className="h-4 w-px bg-slate-800 hidden sm:block" />

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span>Reporting Year:</span>
          <select
            value={reportingYear}
            onChange={(e) => setReportingYear(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value={2024}>2024 (Active)</option>
            <option value={2023}>2023 (Approved)</option>
            <option value={2022}>2022 (Historical)</option>
            <option value={2021}>2021 (Baseline)</option>
          </select>
        </div>
      </div>

      {/* Right: Role Quick-Switcher & Profile */}
      <div className="flex items-center gap-4">
        {/* Role Demo Switcher */}
        <div className="flex items-center gap-2 bg-slate-950/70 border border-slate-800 px-3 py-1.5 rounded-xl">
          <UserCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-[11px] font-medium text-slate-400">Demo Role:</span>
          <div className="relative">
            <select
              value={user?.role || 'ESG Analyst'}
              onChange={handleRoleChange}
              className="bg-transparent text-xs font-semibold text-emerald-400 appearance-none pr-5 cursor-pointer focus:outline-none"
            >
              <option value="Admin" className="bg-slate-900 text-white">Admin</option>
              <option value="Sustainability Manager" className="bg-slate-900 text-white">Sustainability Manager</option>
              <option value="ESG Analyst" className="bg-slate-900 text-white">ESG Analyst</option>
              <option value="Auditor" className="bg-slate-900 text-white">Auditor</option>
              <option value="Supplier" className="bg-slate-900 text-white">Supplier</option>
              <option value="C-Suite" className="bg-slate-900 text-white">C-Suite (Read-Only)</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* User Info */}
        <div className="flex items-center gap-3 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-xs font-bold text-emerald-400">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-medium text-slate-200">{user?.full_name || 'Demo User'}</div>
            <div className="text-[10px] text-slate-400">{user?.role || 'Analyst'}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Logout"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-lg transition-colors ml-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
