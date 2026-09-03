import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  Leaf,
  Layers,
  Users,
  LineChart,
  ShieldCheck,
  Cable,
  Flame,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { UserRole } from '../../types';

interface NavItem {
  name: string;
  to: string;
  icon: React.ReactNode;
  allowedRoles: UserRole[];
}

const navItems: NavItem[] = [
  {
    name: 'Executive Dashboard',
    to: '/dashboard',
    icon: <LayoutDashboard className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'C-Suite'],
  },
  {
    name: 'Organization Model',
    to: '/organization',
    icon: <Building2 className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'C-Suite'],
  },
  {
    name: 'Carbon Accounting',
    to: '/carbon',
    icon: <Leaf className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'C-Suite'],
  },
  {
    name: 'Product LCA & PCF',
    to: '/pcf',
    icon: <Layers className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'Supplier', 'C-Suite'],
  },
  {
    name: 'Supplier Engagement',
    to: '/supplier',
    icon: <Users className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'Supplier', 'C-Suite'],
  },
  {
    name: 'AI Analytics & Scenarios',
    to: '/analytics',
    icon: <LineChart className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'C-Suite'],
  },
  {
    name: 'Compliance & CBAM',
    to: '/compliance',
    icon: <ShieldCheck className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager', 'ESG Analyst', 'Auditor', 'C-Suite'],
  },
  {
    name: 'Integrations & Ingestion',
    to: '/integration',
    icon: <Cable className="w-5 h-5" />,
    allowedRoles: ['Admin', 'Sustainability Manager'],
  },
];

export const Sidebar: React.FC = () => {
  const { user } = useAuthStore();
  const currentRole = (user?.role || 'ESG Analyst') as UserRole;

  const filteredNav = navItems.filter((item) => item.allowedRoles.includes(currentRole));

  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800/80 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-900/30">
          <Flame className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="font-bold text-white tracking-wide text-sm flex items-center gap-1.5">
            Decarb<span className="text-emerald-400">X</span>
          </div>
          <div className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
            Environmental Intelligence
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-5 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Core Modules
        </div>
        {filteredNav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-950'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            {item.icon}
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Governance & Audit Tag */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 m-3 rounded-xl">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-medium text-slate-400">Audit Status</span>
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Verified
          </span>
        </div>
        <div className="text-[10px] text-slate-500 mt-1">
          GHG Protocol & ISO 14067 Engine Active
        </div>
      </div>
    </aside>
  );
};
