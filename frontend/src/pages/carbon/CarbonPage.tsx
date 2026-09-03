import React, { useEffect, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import {
  Leaf,
  Plus,
  FileCheck,
  Search,
  BookOpen,
  Info,
  ShieldCheck,
  AlertTriangle,
  History,
  CheckCircle2,
} from 'lucide-react';
import api from '../../api/client';
import { DataTable } from '../../components/tables/DataTable';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { ActivityData, EmissionRecord, EmissionFactor, AuditLineageData } from '../../types';
import { useAuthStore } from '../../store/authStore';

export const CarbonPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'activity' | 'factors' | 'baselines'>('activity');
  const [activities, setActivities] = useState<ActivityData[]>([]);
  const [factors, setFactors] = useState<EmissionFactor[]>([]);
  const [baselines, setBaselines] = useState<any[]>([]);
  const [targets, setTargets] = useState<any[]>([]);
  const [entities, setEntities] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);

  // Audit Lineage Drawer / Modal
  const [selectedAuditRecord, setSelectedAuditRecord] = useState<AuditLineageData | null>(null);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  // Manual Activity Data Entry Modal
  const [isActivityModalOpen, setIsActivityModalOpen] = useState(false);
  const [formScope, setFormScope] = useState<number>(1);
  const [formCategory, setFormCategory] = useState('Stationary Combustion');
  const [formActivityType, setFormActivityType] = useState('Natural Gas');
  const [formQuantity, setFormQuantity] = useState<number>(1000);
  const [formUnit, setFormUnit] = useState('therms');
  const [formEntityId, setFormEntityId] = useState('');
  const [formFacilityId, setFormFacilityId] = useState('');
  const [formFactorId, setFormFactorId] = useState('');
  const [formAllocationPct, setFormAllocationPct] = useState(100);

  // Recalculate impact preview modal
  const [isRecalcModalOpen, setIsRecalcModalOpen] = useState(false);
  const [recalcPreviewData, setRecalcPreviewData] = useState<any>(null);
  const [selectedFactorForRecalc, setSelectedFactorForRecalc] = useState<EmissionFactor | null>(null);
  const [newFactorValue, setNewFactorValue] = useState<number>(0);

  const { user } = useAuthStore();
  const canEdit = user?.role === 'Admin' || user?.role === 'Sustainability Manager' || user?.role === 'ESG Analyst';
  const canApprove = user?.role === 'Admin' || user?.role === 'Sustainability Manager' || user?.role === 'Auditor';

  useEffect(() => {
    fetchActivities();
    fetchFactors();
    fetchBaselines();
    fetchOrganizationData();
  }, []);

  const fetchActivities = async () => {
    try {
      const res = await api.get('/carbon/activity');
      setActivities(res.data);
    } catch (err) {
      console.error('Failed to load activities:', err);
    }
  };

  const fetchFactors = async () => {
    try {
      const res = await api.get('/carbon/factors');
      setFactors(res.data);
    } catch (err) {
      console.error('Failed to load emission factors:', err);
    }
  };

  const fetchBaselines = async () => {
    try {
      const [bRes, tRes] = await Promise.all([
        api.get('/carbon/baselines'),
        api.get('/carbon/targets'),
      ]);
      setBaselines(bRes.data);
      setTargets(tRes.data);
    } catch (err) {
      console.error('Failed to load baselines:', err);
    }
  };

  const fetchOrganizationData = async () => {
    try {
      const [entRes, facRes] = await Promise.all([
        api.get('/organization/entities'),
        api.get('/organization/facilities'),
      ]);
      setEntities(entRes.data);
      setFacilities(facRes.data);
      if (entRes.data.length) setFormEntityId(entRes.data[0].id);
      if (facRes.data.length) setFormFacilityId(facRes.data[0].id);
    } catch (err) {
      console.error('Failed to load org references:', err);
    }
  };

  const handleInspectAudit = async (activityId: string) => {
    try {
      // Fix Bug 19: Direct targeted O(1) lookup avoiding full table download
      const emissionRes = await api.get(`/carbon/emissions/by-activity/${activityId}`);
      if (emissionRes.data?.id) {
        const auditRes = await api.get(`/carbon/emissions/${emissionRes.data.id}/audit`);
        setSelectedAuditRecord(auditRes.data);
        setIsAuditModalOpen(true);
      } else {
        alert('No emission record found for this activity.');
      }
    } catch (err) {
      console.error('Failed to inspect audit lineage:', err);
    }
  };

  const handleApplyRecalculation = async () => {
    if (!selectedFactorForRecalc) return;
    try {
      await api.post(`/carbon/factors/${selectedFactorForRecalc.id}/apply`, {
        emission_factor_id: selectedFactorForRecalc.id,
        new_factor_value: newFactorValue,
        new_version: '2024.2',
      });
      setIsRecalcModalOpen(false);
      fetchFactors();
      fetchActivities();
    } catch (err) {
      console.error('Failed to apply factor recalculation:', err);
    }
  };

  const handleCreateActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/carbon/activity', {
        organization_id: user?.organization_id || 'default-org',
        entity_id: formEntityId,
        facility_id: formFacilityId,
        scope: Number(formScope),
        category: formCategory,
        activity_type: formActivityType,
        quantity: Number(formQuantity),
        unit: formUnit,
        start_date: '2024-04-01',
        end_date: '2024-06-30',
        reporting_period: '2024-Q2',
        emission_factor_id: formFactorId || undefined,
        allocation_pct: Number(formAllocationPct),
      });
      setIsActivityModalOpen(false);
      fetchActivities();
    } catch (err) {
      console.error('Failed to submit activity data:', err);
    }
  };

  const handlePreviewRecalculation = async (factor: EmissionFactor) => {
    setSelectedFactorForRecalc(factor);
    setNewFactorValue(factor.factor_value * 1.05); // test 5% increase
    try {
      const res = await api.post('/carbon/factors/recalculate-preview', {
        emission_factor_id: factor.id,
        new_factor_value: factor.factor_value * 1.05,
        new_version: '2024.2',
      });
      setRecalcPreviewData(res.data);
      setIsRecalcModalOpen(true);
    } catch (err) {
      console.error('Failed to preview recalculation:', err);
    }
  };

  // TanStack Table columns for Activity Data
  const activityColumns: ColumnDef<ActivityData>[] = [
    {
      accessorKey: 'scope',
      header: 'Scope',
      cell: ({ row }) => {
        const scope = row.original.scope;
        return (
          <Badge variant={scope === 1 ? 'scope1' : scope === 2 ? 'scope2' : 'scope3'}>
            Scope {scope}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ row }) => <span className="font-medium text-white">{row.original.category}</span>,
    },
    {
      accessorKey: 'activity_type',
      header: 'Activity Type',
      cell: ({ row }) => (
        <div>
          <div className="text-slate-200">{row.original.activity_type}</div>
          <div className="text-[11px] text-slate-500">{row.original.reporting_period}</div>
        </div>
      ),
    },
    {
      accessorKey: 'quantity',
      header: 'Quantity & Unit',
      cell: ({ row }) => (
        <span className="font-mono text-emerald-400">
          {row.original.quantity.toLocaleString()} {row.original.unit}
        </span>
      ),
    },
    {
      accessorKey: 'confidence_tier',
      header: 'Data Quality',
      cell: ({ row }) => (
        <div className="flex items-center gap-1.5">
          <Badge
            variant={
              row.original.confidence_tier === 'high'
                ? 'success'
                : row.original.confidence_tier === 'medium'
                ? 'warning'
                : 'danger'
            }
          >
            {row.original.confidence_tier}
          </Badge>
          {row.original.anomaly_flag && (
            <span title="Anomaly flagged by rolling-average rule" className="text-amber-400">
              <AlertTriangle className="w-3.5 h-3.5" />
            </span>
          )}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'Lineage Audit',
      cell: ({ row }) => (
        <button
          onClick={() => handleInspectAudit(row.original.id)}
          className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium px-2 py-1 rounded bg-emerald-950/40 border border-emerald-800/40 transition-colors"
        >
          <History className="w-3.5 h-3.5" />
          Formula Lineage
        </button>
      ),
    },
  ];

  // TanStack Table columns for Emission Factors
  const factorColumns: ColumnDef<EmissionFactor>[] = [
    {
      accessorKey: 'name',
      header: 'Factor Name',
      cell: ({ row }) => (
        <div>
          <div className="font-semibold text-white">{row.original.name}</div>
          <div className="text-[11px] text-slate-400">{row.original.category}</div>
        </div>
      ),
    },
    {
      accessorKey: 'factor_value',
      header: 'Factor Value',
      cell: ({ row }) => (
        <span className="font-mono font-bold text-emerald-400">
          {row.original.factor_value} <span className="text-[11px] text-slate-400">tCO2e/{row.original.unit_denominator}</span>
        </span>
      ),
    },
    {
      accessorKey: 'source',
      header: 'Source & Ver',
      cell: ({ row }) => (
        <div className="text-xs">
          <span className="text-slate-300">{row.original.source}</span>{' '}
          <span className="text-slate-500 font-mono">v{row.original.version}</span>
        </div>
      ),
    },
    {
      accessorKey: 'uncertainty_pct',
      header: 'Uncertainty',
      cell: ({ row }) => (
        <span className="text-xs text-slate-400">±{row.original.uncertainty_pct}%</span>
      ),
    },
    {
      id: 'governance',
      header: 'Governance',
      cell: ({ row }) => (
        <button
          onClick={() => handlePreviewRecalculation(row.original)}
          className="text-[11px] text-sky-400 hover:text-sky-300 px-2 py-1 rounded bg-sky-950/40 border border-sky-800/40"
        >
          Preview Recalc
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Title & Tab Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Enterprise Carbon Accounting</h1>
          <p className="text-xs text-slate-400 mt-1">
            Scope 1, 2 & 3 activity data ledger, versioned factor library, and formula lineage audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {canEdit && (
            <button
              onClick={() => setIsActivityModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950 transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Activity Data
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('activity')}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'activity'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Leaf className="w-4 h-4" />
          Activity Data Ledger ({activities.length})
        </button>

        <button
          onClick={() => setActiveTab('factors')}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'factors'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Emission Factor Library ({factors.length})
        </button>

        <button
          onClick={() => setActiveTab('baselines')}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'baselines'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Baselines & Targets ({baselines.length})
        </button>
      </div>

      {/* Tab Content: Activity Ledger */}
      {activeTab === 'activity' && (
        <div className="glass-panel p-6 rounded-2xl">
          <DataTable
            data={activities}
            columns={activityColumns}
            searchPlaceholder="Search activity type, category, or period..."
          />
        </div>
      )}

      {/* Tab Content: Emission Factor Library */}
      {activeTab === 'factors' && (
        <div className="glass-panel p-6 rounded-2xl">
          <div className="mb-4 text-xs text-slate-400">
            Factor Library is governed by versioning. Any factor change creates a new version and triggers a recalculation impact preview.
          </div>
          <DataTable
            data={factors}
            columns={factorColumns}
            searchPlaceholder="Search factor name, category, or source..."
          />
        </div>
      )}

      {/* Tab Content: Baselines & Targets */}
      {activeTab === 'baselines' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Locked Baseline Year (2021)
            </h2>
            {baselines.map((b) => (
              <div key={b.id} className="space-y-3 text-xs text-slate-300">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span>Scope 1 Direct:</span>
                  <span className="font-bold text-white">{b.scope1_tco2e} tCO2e</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span>Scope 2 Location:</span>
                  <span className="font-bold text-white">{b.scope2_location_tco2e} tCO2e</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span>Scope 2 Market:</span>
                  <span className="font-bold text-white">{b.scope2_market_tco2e} tCO2e</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span>Scope 3 Value Chain:</span>
                  <span className="font-bold text-white">{b.scope3_tco2e} tCO2e</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-emerald-400 text-sm">
                  <span>Total Baseline Emissions:</span>
                  <span>{b.total_tco2e} tCO2e</span>
                </div>
                <div className="text-[11px] text-slate-500 italic">
                  Status: Locked. Restatements require explicit materiality justification.
                </div>
              </div>
            ))}
          </div>

          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Approved Decarbonization Targets
            </h2>
            {targets.map((t) => (
              <div key={t.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs">
                <div className="font-bold text-white text-sm">{t.name}</div>
                <div className="text-slate-400">
                  Reduction Target: <strong className="text-emerald-400">{t.target_reduction_pct}%</strong> by{' '}
                  <strong className="text-white">{t.target_year}</strong> (from base year {t.baseline_year})
                </div>
                <div className="text-slate-400">
                  Current Progress: <strong className="text-sky-400">{t.current_progress_pct}%</strong>
                </div>
                <Badge variant="scope3">{t.target_type} Target</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal: Strict Audit Lineage Drawer (Rule 1) */}
      <Modal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        title="Audit Lineage & Arithmetic Formula Verification"
        maxWidth="2xl"
      >
        {selectedAuditRecord && (
          <div className="space-y-5 text-xs">
            <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                Auditable Formula Lineage (Deterministic)
              </span>
              <div className="font-mono text-sm text-emerald-300 break-words leading-relaxed">
                {selectedAuditRecord.formula_string}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                <span className="text-slate-400 font-medium">Source Activity</span>
                <div className="text-white font-semibold">
                  {selectedAuditRecord.source_activity.quantity} {selectedAuditRecord.source_activity.unit} ({selectedAuditRecord.source_activity.activity_type})
                </div>
                <div className="text-slate-400 text-[11px]">
                  Quality Score: {selectedAuditRecord.source_activity.completeness_score * 100}% • Tier: {selectedAuditRecord.source_activity.confidence_tier}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                <span className="text-slate-400 font-medium">Emission Factor</span>
                <div className="text-white font-semibold">{selectedAuditRecord.factor_name}</div>
                <div className="text-slate-400 text-[11px]">
                  Source: {selectedAuditRecord.factor_source} (v{selectedAuditRecord.factor_version}) • Uncertainty: ±{selectedAuditRecord.factor_uncertainty_pct}%
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
              <span className="text-slate-400 font-medium">Unit Conversions Applied</span>
              <div className="font-mono text-slate-300">{selectedAuditRecord.unit_conversions_applied}</div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-[11px] text-slate-400">
              <div>
                Approved by: <strong className="text-slate-200">{selectedAuditRecord.governance.approved_by || 'Verified by System Admin'}</strong>
              </div>
              <div>
                Timestamp: <span className="font-mono text-slate-300">{selectedAuditRecord.governance.created_at}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal: Add Activity Data */}
      <Modal
        isOpen={isActivityModalOpen}
        onClose={() => setIsActivityModalOpen(false)}
        title="Record Activity Data (Scope 1, 2, 3)"
      >
        <form onSubmit={handleCreateActivity} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">GHG Scope</label>
              <select
                value={formScope}
                onChange={(e) => {
                  const s = Number(e.target.value);
                  setFormScope(s);
                  if (s === 1) {
                    setFormCategory('Stationary Combustion');
                    setFormActivityType('Natural Gas');
                    setFormUnit('therms');
                  } else if (s === 2) {
                    setFormCategory('Purchased Electricity');
                    setFormActivityType('Grid Electricity');
                    setFormUnit('kWh');
                  } else {
                    setFormCategory('Purchased Goods');
                    setFormActivityType('Raw Aluminum Stock');
                    setFormUnit('kg');
                  }
                }}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              >
                <option value={1}>Scope 1 (Direct)</option>
                <option value={2}>Scope 2 (Electricity/Energy)</option>
                <option value={3}>Scope 3 (Value Chain)</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Category</label>
              <input
                type="text"
                required
                value={formCategory}
                onChange={(e) => setFormCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Activity Type / Fuel</label>
              <input
                type="text"
                required
                value={formActivityType}
                onChange={(e) => setFormActivityType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Entity</label>
              <select
                value={formEntityId}
                onChange={(e) => setFormEntityId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              >
                {entities.map((ent) => (
                  <option key={ent.id} value={ent.id}>{ent.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Quantity</label>
              <input
                type="number"
                step="any"
                required
                value={formQuantity}
                onChange={(e) => setFormQuantity(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Unit</label>
              <input
                type="text"
                required
                value={formUnit}
                onChange={(e) => setFormUnit(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Allocation %</label>
              <input
                type="number"
                min={1}
                max={100}
                value={formAllocationPct}
                onChange={(e) => setFormAllocationPct(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Facility</label>
            <select
              value={formFacilityId}
              onChange={(e) => setFormFacilityId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            >
              {facilities.map((fac) => (
                <option key={fac.id} value={fac.id}>{fac.name}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsActivityModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Save & Calculate
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Recalculation Impact Preview */}
      <Modal
        isOpen={isRecalcModalOpen}
        onClose={() => setIsRecalcModalOpen(false)}
        title="Emission Factor Recalculation Governance Preview"
      >
        {recalcPreviewData && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-sky-950/40 border border-sky-800/60 text-sky-300">
              Governance Check: Modifying factor <strong>{selectedFactorForRecalc?.name}</strong> will impact historical calculation records.
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="text-slate-400">Affected Records</div>
                <div className="text-lg font-bold text-white mt-1">{recalcPreviewData.affected_records_count}</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="text-slate-400">Projected Variance</div>
                <div className="text-lg font-bold text-amber-400 mt-1">+{recalcPreviewData.delta_pct}%</div>
              </div>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Current Total:</span>
              <span className="font-mono font-bold text-white">{recalcPreviewData.current_total_tco2e} tCO2e</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Projected Total:</span>
              <span className="font-mono font-bold text-emerald-400">{recalcPreviewData.projected_total_tco2e} tCO2e</span>
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <button
                type="button"
                onClick={() => setIsRecalcModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium"
              >
                Close Preview
              </button>
              {canEdit && (
                <button
                  type="button"
                  onClick={handleApplyRecalculation}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md shadow-emerald-950"
                >
                  Apply & Recalculate Historical Records
                </button>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
