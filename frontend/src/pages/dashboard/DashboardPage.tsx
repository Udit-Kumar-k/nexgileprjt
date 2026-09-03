import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from 'recharts';
import {
  Flame,
  Zap,
  Truck,
  TrendingDown,
  Target as TargetIcon,
  PieChart,
  Building,
  Filter,
  Layers,
} from 'lucide-react';
import api from '../../api/client';
import { StatCard } from '../../components/ui/StatCard';
import { Badge } from '../../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [drilldown, setDrilldown] = useState<any>(null);
  const [carbonFinance, setCarbonFinance] = useState<any>(null);
  const [entities, setEntities] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);
  
  // Drilldown filter states
  const [selectedEntity, setSelectedEntity] = useState<string>('');
  const [selectedFacility, setSelectedFacility] = useState<string>('');
  const [selectedScope, setSelectedScope] = useState<string>('');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExecutiveData();
    fetchOrganizationFilters();
  }, []);

  useEffect(() => {
    fetchOperationalData();
  }, [selectedEntity, selectedFacility, selectedScope, selectedPeriod]);

  const fetchExecutiveData = async () => {
    try {
      const [execRes, finRes] = await Promise.all([
        api.get('/dashboard/executive'),
        api.get('/dashboard/carbon-finance'),
      ]);
      setData(execRes.data);
      setCarbonFinance(finRes.data);
    } catch (err) {
      console.error('Failed to load executive KPIs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganizationFilters = async () => {
    try {
      const [entRes, facRes] = await Promise.all([
        api.get('/organization/entities'),
        api.get('/organization/facilities'),
      ]);
      setEntities(entRes.data);
      setFacilities(facRes.data);
    } catch (err) {
      console.error('Failed to load filters:', err);
    }
  };

  const fetchOperationalData = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedEntity) params.append('entity_id', selectedEntity);
      if (selectedFacility) params.append('facility_id', selectedFacility);
      if (selectedScope) params.append('scope', selectedScope);
      if (selectedPeriod) params.append('period', selectedPeriod);

      const res = await api.get(`/dashboard/operational?${params.toString()}`);
      setDrilldown(res.data);
    } catch (err) {
      console.error('Failed to load drilldown:', err);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  const { summary, target, intensity, carbon_budget, monthly_trend, peer_benchmark } = data;

  return (
    <div className="space-y-8">
      {/* Page Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Executive Carbon Scorecard</h1>
          <p className="text-xs text-slate-400 mt-1">
            Audit-grade consolidation across Scope 1, Scope 2 (Location & Market), and Scope 3 value chain.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success">ISO 14064 Verified</Badge>
          <Badge variant="neutral">GHG Protocol Standard</Badge>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Total Gross Emissions"
          value={summary.total_gross_emissions_tco2e?.toLocaleString()}
          unit="tCO2e"
          change={summary.yoy_change_pct}
          changeLabel="vs 2021 baseline"
          icon={<Flame className="w-4 h-4 text-rose-400" />}
          variant="emerald"
        />

        <StatCard
          title="Scope 1 Direct"
          value={summary.scope1_tco2e?.toLocaleString()}
          unit="tCO2e"
          subtitle="Combustion, fleet & fugitive"
          icon={<Flame className="w-4 h-4 text-amber-400" />}
          variant="amber"
        />

        <StatCard
          title="Scope 2 Market (Net)"
          value={summary.scope2_market_tco2e?.toLocaleString()}
          unit="tCO2e"
          subtitle={`${summary.recs_offset_tco2e || 0} tCO2e offset by RECs`}
          icon={<Zap className="w-4 h-4 text-sky-400" />}
          variant="blue"
        />

        <StatCard
          title="Scope 3 Value Chain"
          value={summary.scope3_tco2e?.toLocaleString()}
          unit="tCO2e"
          subtitle="15 GHG Protocol categories"
          icon={<Truck className="w-4 h-4 text-emerald-400" />}
          variant="emerald"
        />
      </div>

      {/* Secondary Row: Carbon Budget & Intensity Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Carbon Budget Tracker */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <TargetIcon className="w-4 h-4 text-emerald-400" />
              Carbon Budget Tracker
            </h2>
            <Badge variant={carbon_budget.consumed_pct > 85 ? 'warning' : 'success'}>
              {carbon_budget.burn_status}
            </Badge>
          </div>

          <div className="mt-4">
            <div className="flex items-baseline justify-between text-xs text-slate-400">
              <span>Consumed: <strong className="text-white">{carbon_budget.consumed_tco2e} tCO2e</strong></span>
              <span>Cap: <strong className="text-slate-300">{carbon_budget.allocated_budget_tco2e} tCO2e</strong></span>
            </div>

            <div className="w-full h-3 bg-slate-800 rounded-full mt-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, carbon_budget.consumed_pct)}%` }}
              />
            </div>

            <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
              <span>{carbon_budget.consumed_pct}% consumed</span>
              <span className="text-emerald-400">{carbon_budget.remaining_budget_tco2e} tCO2e headroom</span>
            </div>
          </div>

          {/* Intensity KPIs */}
          <div className="mt-6 pt-4 border-t border-slate-800 grid grid-cols-2 gap-3 text-center">
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-[11px] text-slate-400">Revenue Intensity</div>
              <div className="text-base font-bold text-white mt-1">
                {intensity.revenue_intensity_tco2e_per_m} <span className="text-[10px] font-normal text-slate-400">tCO2e/$M</span>
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-[11px] text-slate-400">FTE Intensity</div>
              <div className="text-base font-bold text-white mt-1">
                {intensity.total_intensity_fte} <span className="text-[10px] font-normal text-slate-400">tCO2e/FTE</span>
              </div>
            </div>
          </div>
        </div>

        {/* SBTi Target Trajectory Area Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-emerald-400" />
                {target.target_name}
              </h2>
              <div className="text-xs text-slate-400 mt-0.5">
                Target: {target.target_reduction_pct}% absolute reduction by {target.target_year} ({target.current_progress_pct}% achieved)
              </div>
            </div>
            <Badge variant="scope3">1.5°C Aligned</Badge>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={target.trajectory}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorTarget" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Area type="monotone" dataKey="actual" name="Actual Emissions" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorActual)" />
                <Area type="monotone" dataKey="target" name="SBTi Pathway" stroke="#0ea5e9" strokeDasharray="4 4" strokeWidth={2} fillOpacity={1} fill="url(#colorTarget)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Monthly Trend & Peer Benchmark Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Emissions Trend */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl">
          <h2 className="text-sm font-bold text-white tracking-wide mb-4">Monthly Emissions by Scope (tCO2e)</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="scope1" name="Scope 1 Direct" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
                <Bar dataKey="scope2" name="Scope 2 Electricity" stackId="a" fill="#0ea5e9" radius={[0, 0, 0, 0]} />
                <Bar dataKey="scope3" name="Scope 3 Value Chain" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Peer Benchmark Placeholder Card (Spec requirement) */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Peer Benchmarking</span>
              <Badge variant="neutral">Simulated Cohort</Badge>
            </div>
            <h2 className="text-sm font-bold text-white mt-2">{peer_benchmark.title}</h2>
            <p className="text-xs text-slate-400 mt-1">
              Comparison against 140 peer enterprises in technology hardware & manufacturing sector.
            </p>

            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Your Intensity:</span>
                <span className="font-bold text-emerald-400">{peer_benchmark.user_intensity} tCO2e/$M</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Industry Median:</span>
                <span className="font-semibold text-slate-300">{peer_benchmark.peer_median_intensity} tCO2e/$M</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Top Decile (Best):</span>
                <span className="font-semibold text-sky-400">{peer_benchmark.top_decile_intensity} tCO2e/$M</span>
              </div>
            </div>

            <div className="mt-5 p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
              <span>{peer_benchmark.percentile_rank}</span>
            </div>

            <div className="mt-4 p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/40 text-[11px] text-amber-300/90 leading-relaxed">
              ⚠️ <strong>Simulated Cohort Disclaimer:</strong> Industry benchmarks represent modeled peer percentiles from public disclosures, not verified external audit data.
            </div>
          </div>

          <div className="text-[10px] text-slate-500 pt-4 border-t border-slate-800">
            Source: {peer_benchmark.source}
          </div>
        </div>
      </div>

      {/* Carbon Finance & Offset Registry (Spec Requirement 3.E) */}
      {carbonFinance && (
        <div className="glass-panel p-6 rounded-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-wide">
                  Carbon Finance, Shadow Pricing & Offset Registry
                </h2>
                <Badge variant="success">TCFD Aligned</Badge>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Internal carbon fee of ${carbonFinance.internal_carbon_pricing.price_per_tco2e_usd}/tCO2e applied across balance sheet operations.
              </p>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Total Carbon Liability</span>
              <div className="text-xl font-bold font-mono text-emerald-400">
                ${carbonFinance.internal_carbon_pricing.total_liability_usd.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <span className="text-slate-400 font-semibold">Scope 1 Direct Liability:</span>
              <div className="text-lg font-bold font-mono text-white">
                ${carbonFinance.internal_carbon_pricing.scope1_liability_usd.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-500">Fleet & Stationary combustion shadow cost</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <span className="text-slate-400 font-semibold">Scope 2 Electricity Liability:</span>
              <div className="text-lg font-bold font-mono text-white">
                ${carbonFinance.internal_carbon_pricing.scope2_liability_usd.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-500">Market-based net residual grid tariffs</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <span className="text-slate-400 font-semibold">Scope 3 Value Chain Liability:</span>
              <div className="text-lg font-bold font-mono text-white">
                ${carbonFinance.internal_carbon_pricing.scope3_liability_usd.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-500">Purchased goods & logistics exposure</div>
            </div>
          </div>

          {/* Verified Carbon Offsets Registry Table */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Verified Carbon Credit / Offset Registry (Residual Neutrality)
            </span>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Project Name</th>
                    <th className="p-2.5">Standard & Vintage</th>
                    <th className="p-2.5">Volume (tCO2e)</th>
                    <th className="p-2.5">Price ($/t)</th>
                    <th className="p-2.5">Status</th>
                    <th className="p-2.5 text-right">Retirement Serial</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70 text-slate-300">
                  {carbonFinance.offset_registry.map((off: any) => (
                    <tr key={off.id} className="hover:bg-slate-800/30">
                      <td className="p-2.5 font-medium text-white">{off.project_name}</td>
                      <td className="p-2.5">{off.standard} ({off.vintage})</td>
                      <td className="p-2.5 font-mono text-emerald-400 font-bold">{off.volume_tco2e} t</td>
                      <td className="p-2.5 font-mono">${off.price_usd_per_t}</td>
                      <td className="p-2.5"><Badge variant="success">{off.retirement_status}</Badge></td>
                      <td className="p-2.5 font-mono text-slate-400 text-right text-[11px]">{off.serial_number}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Operational Drill-down Section */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
              <Filter className="w-4 h-4 text-emerald-400" />
              Operational Drill-Down & Filters
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Filter carbon records dynamically across legal entities, facilities, scopes, and time periods.
            </p>
          </div>
          <div className="text-xs font-semibold text-emerald-400 bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-800/40">
            Filtered Total: {drilldown?.filtered_total_tco2e || 0} tCO2e ({drilldown?.records_count || 0} records)
          </div>
        </div>

        {/* Filter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Entity</label>
            <select
              value={selectedEntity}
              onChange={(e) => setSelectedEntity(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Entities</option>
              {entities.map((ent) => (
                <option key={ent.id} value={ent.id}>{ent.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Facility</label>
            <select
              value={selectedFacility}
              onChange={(e) => setSelectedFacility(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Facilities</option>
              {facilities.map((fac) => (
                <option key={fac.id} value={fac.id}>{fac.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Scope</label>
            <select
              value={selectedScope}
              onChange={(e) => setSelectedScope(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Scopes</option>
              <option value="1">Scope 1 (Direct)</option>
              <option value="2">Scope 2 (Electricity)</option>
              <option value="3">Scope 3 (Value Chain)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Period</label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Periods</option>
              {['2023-Q1', '2023-Q2', '2023-Q3', '2023-Q4', '2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4', '2025-Q1', '2025-Q2'].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Drilldown Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Emissions by Facility</h3>
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={drilldown?.by_facility || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis type="number" stroke="#64748b" fontSize={10} />
                  <YAxis type="category" dataKey="facility" stroke="#64748b" fontSize={10} width={130} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                  <Bar dataKey="emissions_tco2e" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Emissions by Activity Category</h3>
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={drilldown?.by_category || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="category" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                  <Bar dataKey="emissions_tco2e" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
