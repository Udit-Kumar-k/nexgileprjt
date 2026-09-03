import React, { useEffect, useState } from 'react';
import {
  LineChart as LineChartIcon,
  Zap,
  Sliders,
  AlertTriangle,
  TrendingDown,
  CheckCircle2,
  Shield,
  Plus,
} from 'lucide-react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import api from '../../api/client';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { useAuthStore } from '../../store/authStore';

export const AnalyticsPage: React.FC = () => {
  const [paretoData, setParetoData] = useState<any[]>([]);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [initiatives, setInitiatives] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);

  // What-if simulator levers state
  const [scope1Lever, setScope1Lever] = useState<number>(30); // 30% reduction on fleet/combustion
  const [scope2Lever, setScope2Lever] = useState<number>(60); // 60% reduction via renewables
  const [scope3Lever, setScope3Lever] = useState<number>(20); // 20% reduction via supplier circularity
  const [simulationResult, setSimulationResult] = useState<any>(null);

  // Scenario creation modal
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false);
  const [scenarioName, setScenarioName] = useState('');
  const [scenarioDesc, setScenarioDesc] = useState('');

  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();
  const canEdit = user?.role === 'Admin' || user?.role === 'Sustainability Manager' || user?.role === 'ESG Analyst';

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  useEffect(() => {
    runSimulation();
  }, [scope1Lever, scope2Lever, scope3Lever]);

  const fetchAnalyticsData = async () => {
    try {
      const [pRes, sRes, iRes, aRes] = await Promise.all([
        api.get('/analytics/pareto'),
        api.get('/analytics/scenarios'),
        api.get('/analytics/initiatives'),
        api.get('/analytics/anomalies'),
      ]);
      setParetoData(pRes.data);
      setScenarios(sRes.data);
      setInitiatives(iRes.data);
      setAnomalies(aRes.data);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    try {
      const res = await api.post('/analytics/scenarios/simulate', {
        baseline_year: 2023,
        levers: [
          { name: 'Fleet & Combustion Decarb', scope: 1, reduction_pct: scope1Lever },
          { name: 'Renewable Power Contracts', scope: 2, reduction_pct: scope2Lever },
          { name: 'Supplier Circular Sourcing', scope: 3, reduction_pct: scope3Lever },
        ],
      });
      setSimulationResult(res.data);
    } catch (err) {
      console.error('Failed to simulate scenario:', err);
    }
  };

  const handleSaveScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/analytics/scenarios', {
        organization_id: user?.organization_id || 'default-org',
        name: scenarioName,
        description: scenarioDesc,
        baseline_year: 2023,
        target_year: 2030,
        levers: [
          { name: 'Fleet & Combustion Decarb', scope: 1, reduction_pct: scope1Lever },
          { name: 'Renewable Power Contracts', scope: 2, reduction_pct: scope2Lever },
          { name: 'Supplier Circular Sourcing', scope: 3, reduction_pct: scope3Lever },
        ],
      });
      setIsScenarioModalOpen(false);
      setScenarioName('');
      setScenarioDesc('');
      fetchAnalyticsData();
    } catch (err) {
      console.error('Failed to save scenario:', err);
    }
  };

  const handleResolveAnomaly = async (id: string) => {
    try {
      await api.put(`/analytics/anomalies/${id}/resolve`, {
        status: 'resolved',
        resolution_notes: 'Reviewed with facility engineer; confirmed meter recalibration.',
      });
      fetchAnalyticsData();
    } catch (err) {
      console.error('Failed to resolve anomaly:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Analytics & Reduction Planning</h1>
          <p className="text-xs text-slate-400 mt-1">
            Pareto emission hotspot analysis, isolated what-if scenario forecasting, and statistical rolling-average anomaly detection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="success">Scenario Isolation Active</Badge>
        </div>
      </div>

      {/* Row 1: Hotspot Pareto Chart */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">Hotspot Pareto Analysis (80/20 Rule)</h2>
            <div className="text-xs text-slate-400">
              Categories ranked by absolute emissions with cumulative percentage contribution curve.
            </div>
          </div>
          <Badge variant="scope3">Top Emissions Sources</Badge>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={paretoData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
              <YAxis yAxisId="left" stroke="#64748b" fontSize={11} />
              <YAxis yAxisId="right" orientation="right" stroke="#10b981" unit="%" fontSize={11} domain={[0, 100]} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar yAxisId="left" dataKey="emissions_tco2e" name="Emissions (tCO2e)" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="cumulative_pct" name="Cumulative %" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2: What-If Scenario Builder (Strict Rule 3: Isolated from Actuals) */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Interactive What-If Scenario Simulator
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly isolated in DB (`is_scenario = True`). Forecasts never modify approved actuals.
            </p>
          </div>

          {canEdit && (
            <button
              onClick={() => setIsScenarioModalOpen(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all self-start"
            >
              <Plus className="w-4 h-4" />
              Save Scenario
            </button>
          )}
        </div>

        {/* Levers Sliders & Simulation Results */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sliders on left */}
          <div className="lg:col-span-1 space-y-5">
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-slate-300">Scope 1: Fleet & Fuel Electrification</span>
                <span className="text-amber-400 font-mono">{scope1Lever}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={scope1Lever}
                onChange={(e) => setScope1Lever(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-slate-300">Scope 2: 100% Renewable PPA Contracts</span>
                <span className="text-sky-400 font-mono">{scope2Lever}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={scope2Lever}
                onChange={(e) => setScope2Lever(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-slate-300">Scope 3: Low-Carbon Steel & Materials</span>
                <span className="text-emerald-400 font-mono">{scope3Lever}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={scope3Lever}
                onChange={(e) => setScope3Lever(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>
          </div>

          {/* Results Card on right */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Baseline Actuals</span>
              <div className="text-2xl font-bold text-white font-mono">
                {simulationResult?.baseline_total_tco2e?.toLocaleString()} <span className="text-xs font-normal text-slate-400">tCO2e</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Projected Net Emissions</span>
              <div className="text-2xl font-bold text-emerald-400 font-mono">
                {simulationResult?.projected_total_tco2e?.toLocaleString()} <span className="text-xs font-normal text-slate-400">tCO2e</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-center space-y-1">
              <span className="text-[11px] font-semibold text-emerald-400 uppercase">Projected Reduction</span>
              <div className="text-2xl font-bold text-emerald-300 font-mono">
                -{simulationResult?.overall_reduction_pct}%
              </div>
              <div className="text-[10px] text-slate-400">
                ({simulationResult?.total_reduction_tco2e?.toLocaleString()} tCO2e avoided)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Reduction Initiatives & Anomaly Resolution Center */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Reduction Initiatives Tracker */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Enterprise Decarbonization Initiatives ({initiatives.length})
          </h2>
          <div className="space-y-3">
            {initiatives.map((init) => (
              <div key={init.id} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs">{init.name}</span>
                  <Badge variant={init.status === 'completed' ? 'success' : 'info'}>{init.status}</Badge>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Lever: <strong className="text-slate-300">{init.lever_type}</strong></span>
                  <span className="font-mono text-emerald-400">
                    {init.actual_reduction_tco2e} / {init.target_reduction_tco2e} tCO2e
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-850">
                  <span>Capex: ${init.capex_usd?.toLocaleString()}</span>
                  <span>Payback: {init.payback_years} yrs</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Statistical Anomaly Detection Alert Center */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Statistical Anomaly Alert Center ({anomalies.filter((a) => a.status === 'flagged').length} flagged)
            </h2>
            <Badge variant="warning">3-Month Rolling Rule</Badge>
          </div>

          <div className="space-y-3">
            {anomalies.map((anom) => (
              <div key={anom.id} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs">{anom.facility_name}</span>
                  <Badge variant={anom.status === 'resolved' ? 'success' : 'danger'}>{anom.status}</Badge>
                </div>
                <div className="text-xs text-slate-400">
                  Metric: <strong className="text-white">{anom.metric_name}</strong> • Variance:{' '}
                  <strong className="text-rose-400 font-mono">+{anom.deviation_pct}%</strong> vs rolling average
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-850">
                  <span>Actual: {anom.actual_value} (Expected: {anom.expected_value})</span>
                  {anom.status === 'flagged' && canEdit && (
                    <button
                      onClick={() => handleResolveAnomaly(anom.id)}
                      className="text-emerald-400 hover:text-emerald-300 font-medium px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/40"
                    >
                      Resolve Anomaly
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Modal: Save Scenario */}
      <Modal
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
        title="Save Forecast Scenario Model"
      >
        <form onSubmit={handleSaveScenario} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Scenario Title</label>
            <input
              type="text"
              required
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              placeholder="e.g. Accelerated 2028 Net Zero Path"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Description</label>
            <textarea
              value={scenarioDesc}
              onChange={(e) => setScenarioDesc(e.target.value)}
              rows={3}
              placeholder="Key assumptions and capital allocation details..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-400">
            Selected Levers: Scope 1 ({scope1Lever}%), Scope 2 ({scope2Lever}%), Scope 3 ({scope3Lever}%)
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsScenarioModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Save Scenario
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
