import React, { useEffect, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import {
  Users,
  Mail,
  Award,
  CheckCircle2,
  Clock,
  Send,
  Plus,
  Filter,
  FileCheck,
  TrendingDown,
} from 'lucide-react';
import api from '../../api/client';
import { DataTable } from '../../components/tables/DataTable';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { SupplierItem, ActionPlanResponse } from '../../types';
import { useAuthStore } from '../../store/authStore';

export const SupplierPage: React.FC = () => {
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [actionPlans, setActionPlans] = useState<any[]>([]);
  const [questionnaires, setQuestionnaires] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Invite modal
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteName, setInviteName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteCategory, setInviteCategory] = useState('Raw Materials');
  const [inviteCountry, setInviteCountry] = useState('United States');
  const [inviteTier, setInviteTier] = useState('Tier 1');

  // Supplier Portal Response Modal
  const [isPortalModalOpen, setIsPortalModalOpen] = useState(false);
  const [selectedSupplierForPortal, setSelectedSupplierForPortal] = useState<SupplierItem | null>(null);
  const [attestationName, setAttestationName] = useState('');

  // Action plan modal
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [actionSupplierId, setActionSupplierId] = useState('');
  const [actionName, setActionName] = useState('');
  const [actionReduction, setActionReduction] = useState(150);

  const { user } = useAuthStore();
  const isSupplierRole = user?.role === 'Supplier';
  const canEdit = user?.role === 'Admin' || user?.role === 'Sustainability Manager' || user?.role === 'ESG Analyst';

  useEffect(() => {
    fetchSuppliers();
    fetchActionPlans();
    fetchQuestionnaires();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const res = await api.get('/supplier/suppliers');
      setSuppliers(res.data);
    } catch (err) {
      console.error('Failed to load suppliers:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchActionPlans = async () => {
    try {
      const res = await api.get('/supplier/action-plans');
      setActionPlans(res.data);
    } catch (err) {
      console.error('Failed to load action plans:', err);
    }
  };

  const fetchQuestionnaires = async () => {
    try {
      const res = await api.get('/supplier/questionnaires');
      setQuestionnaires(res.data);
    } catch (err) {
      console.error('Failed to load questionnaires:', err);
    }
  };

  const handleInviteSupplier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/supplier/invite', {
        supplier_name: inviteName,
        email: inviteEmail,
        category: inviteCategory,
        country: inviteCountry,
        tier: inviteTier,
      });
      setIsInviteModalOpen(false);
      setInviteName('');
      setInviteEmail('');
      fetchSuppliers();
    } catch (err) {
      console.error('Failed to invite supplier:', err);
    }
  };

  const handleSubmitPortalData = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSupplierForPortal || !questionnaires.length) return;
    try {
      await api.post('/supplier/submissions', {
        questionnaire_id: questionnaires[0].id,
        supplier_id: selectedSupplierForPortal.id,
        responses: {
          q1_scope12: true,
          q2_renewables: 65,
          q3_sbti: true,
          q4_intensity: 18.2,
        },
        attestation_name: attestationName || user?.full_name,
        status: 'submitted',
      });
      setIsPortalModalOpen(false);
      fetchSuppliers();
    } catch (err) {
      console.error('Failed to submit questionnaire:', err);
    }
  };

  const handleCreateActionPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/supplier/action-plans', {
        supplier_id: actionSupplierId || (suppliers[0] ? suppliers[0].id : ''),
        initiative_name: actionName,
        target_reduction_tco2e: Number(actionReduction),
        due_date: '2025-12-31',
        status: 'in_progress',
        assigned_to: user?.email,
      });
      setIsActionModalOpen(false);
      setActionName('');
      fetchActionPlans();
    } catch (err) {
      console.error('Failed to create action plan:', err);
    }
  };

  const columns: ColumnDef<SupplierItem>[] = [
    {
      accessorKey: 'name',
      header: 'Supplier & Code',
      cell: ({ row }) => (
        <div>
          <div className="font-semibold text-white">{row.original.name}</div>
          <div className="text-[11px] font-mono text-emerald-400">{row.original.code}</div>
        </div>
      ),
    },
    {
      accessorKey: 'tier',
      header: 'Tier & Country',
      cell: ({ row }) => (
        <div>
          <Badge variant="neutral">{row.original.tier}</Badge>
          <div className="text-[11px] text-slate-400 mt-1">📍 {row.original.country}</div>
        </div>
      ),
    },
    {
      accessorKey: 'category',
      header: 'Category & Spend',
      cell: ({ row }) => (
        <div>
          <div className="text-slate-300 font-medium">{row.original.category}</div>
          <div className="text-[11px] text-slate-400">${(row.original.spend_usd / 1000000).toFixed(2)}M Spend</div>
        </div>
      ),
    },
    {
      accessorKey: 'onboarding_status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge
          variant={
            row.original.onboarding_status === 'verified'
              ? 'success'
              : row.original.onboarding_status === 'submitted'
              ? 'info'
              : 'warning'
          }
        >
          {row.original.onboarding_status}
        </Badge>
      ),
    },
    {
      id: 'scorecard',
      header: 'ESG Scorecard',
      cell: ({ row }) => {
        const sc = row.original.scorecard;
        if (!sc) return <span className="text-slate-500 text-xs">Pending</span>;
        return (
          <div className="flex items-center gap-2">
            <span
              className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs ${
                sc.rating === 'A'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-700'
                  : sc.rating === 'B'
                  ? 'bg-sky-950 text-sky-400 border border-sky-700'
                  : 'bg-amber-950 text-amber-400 border border-amber-700'
              }`}
            >
              {sc.rating}
            </span>
            <div>
              <div className="text-xs font-semibold text-white">{sc.maturity_score}/100</div>
              <div className="text-[10px] text-emerald-400 font-medium">{sc.yoy_change_pct}% YoY</div>
            </div>
          </div>
        );
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setSelectedSupplierForPortal(row.original);
              setIsPortalModalOpen(true);
            }}
            className="text-xs text-sky-400 hover:text-sky-300 font-medium px-2 py-1 rounded bg-sky-950/40 border border-sky-800/40"
          >
            Portal Form
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Supplier Engagement & Scope 3</h1>
          <p className="text-xs text-slate-400 mt-1">
            Supplier onboarding, materiality questionnaires, primary emissions scorecards, and joint decarbonization action plans.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {canEdit && (
            <>
              <button
                onClick={() => setIsActionModalOpen(true)}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
              >
                <Plus className="w-4 h-4 text-emerald-400" />
                New Action Plan
              </button>
              <button
                onClick={() => setIsInviteModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950 transition-all"
              >
                <Mail className="w-4 h-4" />
                Invite Supplier
              </button>
            </>
          )}
        </div>
      </div>

      {/* Supplier Ranking & Scorecard Table */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Supplier ESG Performance Ledger ({suppliers.length})
          </h2>
          <Badge variant="scope3">Scope 3 Cat 1 Focus</Badge>
        </div>

        <DataTable
          data={suppliers}
          columns={columns}
          searchPlaceholder="Search supplier name, country, or category..."
        />
      </div>

      {/* Joint Decarbonization Action Plans Grid */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
          Active Supplier Decarbonization Action Plans ({actionPlans.length})
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {actionPlans.map((plan) => (
            <div key={plan.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <span className="font-bold text-white text-xs">{plan.initiative_name}</span>
                <Badge variant={plan.status === 'completed' ? 'success' : 'info'}>{plan.status}</Badge>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-850">
                <span>Target Reduction:</span>
                <span className="font-mono font-bold text-emerald-400">-{plan.target_reduction_tco2e} tCO2e</span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span>Due Date: {plan.due_date}</span>
                <span className="truncate max-w-[120px]">Assignee: {plan.assigned_to || 'Assigned'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal: Invite Supplier */}
      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        title="Invite Supplier to DecarbX Portal"
      >
        <form onSubmit={handleInviteSupplier} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Company Name</label>
            <input
              type="text"
              required
              value={inviteName}
              onChange={(e) => setInviteName(e.target.value)}
              placeholder="e.g. Foxconn Technologies"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Contact Email</label>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="sustainability@supplier.com"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Category</label>
              <select
                value={inviteCategory}
                onChange={(e) => setInviteCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="Raw Materials">Raw Materials</option>
                <option value="Electronics">Electronics</option>
                <option value="Packaging">Packaging</option>
                <option value="Logistics">Logistics</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Country</label>
              <input
                type="text"
                required
                value={inviteCountry}
                onChange={(e) => setInviteCountry(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsInviteModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Send Invitation
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Primary Data Form & Attestation */}
      <Modal
        isOpen={isPortalModalOpen}
        onClose={() => setIsPortalModalOpen(false)}
        title={`Supplier Carbon Disclosure: ${selectedSupplierForPortal?.name}`}
      >
        <form onSubmit={handleSubmitPortalData} className="space-y-4 text-xs">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 space-y-1">
            <div className="font-semibold text-white">Materiality Assessment Standard</div>
            <div>Please provide your primary Scope 1 & 2 emissions data and sign the digital attestation.</div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Scope 1 & 2 Emissions (tCO2e)</label>
            <input
              type="number"
              defaultValue={1420}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Renewable Electricity Share (%)</label>
            <input
              type="number"
              min={0}
              max={100}
              defaultValue={75}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Digital Attestation & Authorized Signatory</label>
            <input
              type="text"
              required
              value={attestationName}
              onChange={(e) => setAttestationName(e.target.value)}
              placeholder="e.g. Dr. Wei Zhang, Chief Environmental Officer"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsPortalModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Submit Attestation
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: New Action Plan */}
      <Modal
        isOpen={isActionModalOpen}
        onClose={() => setIsActionModalOpen(false)}
        title="Assign Decarbonization Action Plan"
      >
        <form onSubmit={handleCreateActionPlan} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Select Supplier</label>
            <select
              value={actionSupplierId}
              onChange={(e) => setActionSupplierId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            >
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.tier})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Initiative Name</label>
            <input
              type="text"
              required
              value={actionName}
              onChange={(e) => setActionName(e.target.value)}
              placeholder="e.g. On-site solar rooftop installation"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Reduction (tCO2e)</label>
            <input
              type="number"
              required
              value={actionReduction}
              onChange={(e) => setActionReduction(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsActionModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Assign Initiative
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
