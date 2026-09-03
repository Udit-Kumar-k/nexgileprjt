import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { AICopilotDrawer } from '../ai/AICopilotDrawer';
import { useAuthStore } from '../../store/authStore';
import { ShieldCheck, Building2, Briefcase } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="flex min-h-screen bg-slate-950">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />

        {/* Role-Specific Workspace Context Banners */}
        {user?.role === 'Supplier' && (
          <div className="bg-gradient-to-r from-amber-950/70 via-slate-900 to-amber-950/70 border-b border-amber-800/40 px-6 py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-amber-300 font-medium">
              <Building2 className="w-4 h-4 text-amber-400" />
              <span>
                <strong>Supplier Self-Service Portal Active:</strong> Session for Foxconn Technologies Inc. (Code: SUP-001 • Primary Tier 1 Supplier)
              </span>
            </div>
            <span className="hidden sm:inline text-slate-400 text-[11px]">
              Access restricted to questionnaires, primary activity submissions & action plans
            </span>
          </div>
        )}

        {user?.role === 'Auditor' && (
          <div className="bg-gradient-to-r from-sky-950/70 via-slate-900 to-sky-950/70 border-b border-sky-800/40 px-6 py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-sky-300 font-medium">
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>
                <strong>Independent Assurance Workspace:</strong> Read-only access with formula arithmetic inspection and verification controls
              </span>
            </div>
            <span className="hidden sm:inline text-slate-400 text-[11px]">
              PwC ESG Assurance Engagement 2024
            </span>
          </div>
        )}

        {user?.role === 'C-Suite' && (
          <div className="bg-gradient-to-r from-emerald-950/60 via-slate-900 to-emerald-950/60 border-b border-emerald-800/40 px-6 py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-emerald-300 font-medium">
              <Briefcase className="w-4 h-4 text-emerald-400" />
              <span>
                <strong>Executive Climate Briefing & Carbon Finance Mode:</strong> High-level scorecards, $65/tCO2e internal pricing & board summaries
              </span>
            </div>
            <span className="hidden sm:inline text-slate-400 text-[11px]">
              SBTi 1.5°C Trajectory Aligned
            </span>
          </div>
        )}

        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          <Outlet />
        </main>

        {/* Global AI Copilot Assistant Drawer */}
        <AICopilotDrawer />
      </div>
    </div>
  );
};
