import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, Shield, ArrowRight, CheckCircle2 } from 'lucide-react';
import api from '../../api/client';
import { useAuthStore } from '../../store/authStore';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('admin@nexgile.com');
  const [password, setPassword] = useState('DecarbX2024!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post('/auth/login', { email, password });
      const { access_token, user } = res.data;
      setAuth(user, access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const demoRoles = [
    { name: 'Admin', email: 'admin@nexgile.com', desc: 'Full system & tenant control' },
    { name: 'Sustainability Manager', email: 'sustainability@nexgile.com', desc: 'Factor governance & targets' },
    { name: 'ESG Analyst', email: 'analyst@nexgile.com', desc: 'Data entry & calculations' },
    { name: 'Auditor', email: 'auditor@pwc-assurance.com', desc: 'Lineage inspection & signoff' },
    { name: 'Supplier', email: 'supplier@foxconn-tech.com', desc: 'Primary data portal & scorecards' },
    { name: 'C-Suite', email: 'csuite@nexgile.com', desc: 'Executive read-only analytics' },
  ];

  const quickFill = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('DecarbX2024!');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8 z-10">
        {/* Left: Platform Overview */}
        <div className="flex flex-col justify-between py-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-xl shadow-emerald-950">
                <Flame className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-white tracking-tight">
                  Decarb<span className="text-emerald-400">X</span>
                </h1>
                <p className="text-xs uppercase tracking-widest font-semibold text-slate-400">
                  Environmental Intelligence
                </p>
              </div>
            </div>

            <h2 className="mt-8 text-3xl font-bold text-white leading-tight">
              Audit-grade carbon accounting & product footprinting.
            </h2>
            <p className="mt-4 text-sm text-slate-400 leading-relaxed">
              Consolidate Scope 1, 2, and 3 activities, calculate ISO 14067 Product Carbon Footprints,
              engage suppliers, and report to CSRD and CBAM with mathematically verifiable formula lineage.
            </p>

            <div className="mt-8 space-y-3">
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Deterministic calculation engine with full formula audit string</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Strict scenario isolation protecting actuals from what-if models</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Supabase PostgreSQL architecture with zero external paid APIs</span>
              </div>
            </div>
          </div>

          <div className="text-xs text-slate-500 pt-6">
            Nexgile DecarbX Platform v1.0 • Enterprise Edition
          </div>
        </div>

        {/* Right: Login Card & Demo Role Selectors */}
        <div className="glass-panel p-8 rounded-2xl shadow-2xl border border-slate-800">
          <h3 className="text-lg font-bold text-white tracking-wide">Sign In to Platform</h3>
          <p className="text-xs text-slate-400 mt-1">Select a role below for instant demo credentials.</p>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="mt-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Corporate Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-sm font-semibold tracking-wide flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition-all disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Access DecarbX'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Quick Role Login (Click to populate)
            </div>
            <div className="grid grid-cols-2 gap-2">
              {demoRoles.map((r) => (
                <button
                  key={r.name}
                  type="button"
                  onClick={() => quickFill(r.email)}
                  className={`p-2 rounded-lg text-left text-xs border transition-all ${
                    email === r.email
                      ? 'border-emerald-500/80 bg-emerald-950/40 text-emerald-300'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold truncate">{r.name}</div>
                  <div className="text-[10px] text-slate-500 truncate">{r.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
