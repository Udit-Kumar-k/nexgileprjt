import React, { useEffect, useState } from 'react';
import {
  Building2,
  Building,
  Factory,
  FolderTree,
  Coins,
  ChevronRight,
  ChevronDown,
  Plus,
  ShieldAlert,
  Percent,
} from 'lucide-react';
import api from '../../api/client';
import { HierarchyTreeNode } from '../../types';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { useAuthStore } from '../../store/authStore';

export const OrganizationPage: React.FC = () => {
  const [tree, setTree] = useState<HierarchyTreeNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [boundaries, setBoundaries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Entity creation modal
  const [isEntityModalOpen, setIsEntityModalOpen] = useState(false);
  const [entityName, setEntityName] = useState('');
  const [entityCode, setEntityCode] = useState('');
  const [entityCountry, setEntityCountry] = useState('United States');
  const [consolidationMethod, setConsolidationMethod] = useState('Operational Control');
  const [ownershipPct, setOwnershipPct] = useState(100);

  const { user } = useAuthStore();
  const canEdit = user?.role === 'Admin' || user?.role === 'Sustainability Manager';

  useEffect(() => {
    fetchTree();
    fetchBoundaries();
  }, []);

  const fetchTree = async () => {
    try {
      const res = await api.get('/organization/tree');
      setTree(res.data);
      // Auto-expand all top nodes
      const initialExpanded: Record<string, boolean> = {};
      const expandRecursive = (nodes: HierarchyTreeNode[]) => {
        nodes.forEach((n) => {
          initialExpanded[n.id] = true;
          if (n.children) expandRecursive(n.children);
        });
      };
      expandRecursive(res.data);
      setExpandedNodes(initialExpanded);
    } catch (err) {
      console.error('Failed to load hierarchy tree:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBoundaries = async () => {
    try {
      const res = await api.get('/organization/boundaries');
      setBoundaries(res.data);
    } catch (err) {
      console.error('Failed to load boundaries:', err);
    }
  };

  const toggleNode = (id: string) => {
    setExpandedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCreateEntity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tree.length) return;
    try {
      await api.post('/organization/entities', {
        organization_id: tree[0].id,
        name: entityName,
        code: entityCode,
        country: entityCountry,
        consolidation_method: consolidationMethod,
        ownership_percentage: ownershipPct,
      });
      setIsEntityModalOpen(false);
      setEntityName('');
      setEntityCode('');
      fetchTree();
    } catch (err) {
      console.error('Failed to create entity:', err);
    }
  };

  const renderNodeIcon = (type: string) => {
    switch (type) {
      case 'organization':
        return <Building2 className="w-4 h-4 text-emerald-400" />;
      case 'entity':
        return <Building className="w-4 h-4 text-sky-400" />;
      case 'facility':
        return <Factory className="w-4 h-4 text-amber-400" />;
      case 'department':
        return <FolderTree className="w-4 h-4 text-indigo-400" />;
      case 'cost_center':
        return <Coins className="w-4 h-4 text-emerald-400" />;
      default:
        return <Building className="w-4 h-4 text-slate-400" />;
    }
  };

  const renderTree = (nodes: HierarchyTreeNode[], depth = 0) => {
    return (
      <div className={`space-y-1.5 ${depth > 0 ? 'ml-6 pl-4 border-l border-slate-800' : ''}`}>
        {nodes.map((node) => {
          const isExpanded = expandedNodes[node.id];
          const hasChildren = node.children && node.children.length > 0;

          return (
            <div key={node.id} className="space-y-1.5">
              <div
                onClick={() => hasChildren && toggleNode(node.id)}
                className={`flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer ${
                  node.type === 'organization'
                    ? 'bg-slate-900/90 border-slate-700/80 shadow-md'
                    : node.type === 'entity'
                    ? 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    : 'bg-slate-950/40 border-slate-850 hover:border-slate-750'
                }`}
              >
                <div className="flex items-center gap-3">
                  {hasChildren ? (
                    <button className="text-slate-500 hover:text-white">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                  ) : (
                    <div className="w-4" />
                  )}

                  {renderNodeIcon(node.type)}

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-white">{node.name}</span>
                      <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 font-mono">
                        {node.code}
                      </span>
                    </div>

                    {node.metadata && (
                      <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
                        {node.metadata.country && <span>📍 {node.metadata.country}</span>}
                        {node.metadata.consolidation && (
                          <span>⚖️ {node.metadata.consolidation}</span>
                        )}
                        {node.metadata.ownership && (
                          <span>📊 {node.metadata.ownership}% Ownership</span>
                        )}
                        {node.metadata.type && <span>🏭 {node.metadata.type}</span>}
                        {node.metadata.grid_region && (
                          <span>⚡ {node.metadata.grid_region}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <Badge
                  variant={
                    node.type === 'organization'
                      ? 'success'
                      : node.type === 'entity'
                      ? 'info'
                      : node.type === 'facility'
                      ? 'warning'
                      : 'neutral'
                  }
                  size="sm"
                >
                  {node.type.replace('_', ' ')}
                </Badge>
              </div>

              {isExpanded && hasChildren && renderTree(node.children!, depth + 1)}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Organization Model</h1>
          <p className="text-xs text-slate-400 mt-1">
            Hierarchy tree view, consolidation boundaries, and facility ownership across the corporate enterprise.
          </p>
        </div>

        {canEdit && (
          <button
            onClick={() => setIsEntityModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950 transition-all self-start"
          >
            <Plus className="w-4 h-4" />
            Add Legal Entity
          </button>
        )}
      </div>

      {/* Grid: Hierarchy Tree on left, Reporting Boundaries on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Interactive Tree View */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-emerald-400" />
              Organizational Hierarchy Tree
            </h2>
            <span className="text-xs text-slate-500">
              Organization → Entity → Facility → Department → Cost Center
            </span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-500" />
            </div>
          ) : (
            renderTree(tree)
          )}
        </div>

        {/* Right: Reporting Boundaries & Rules */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              GHG Protocol Consolidation
            </h2>
            <div className="space-y-3 text-xs text-slate-300">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="font-semibold text-white">Operational Control Approach</div>
                <div className="text-slate-400 mt-1">
                  100% of GHG emissions accounted for all entities and facilities where the enterprise has authority to introduce and implement operating policies.
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="font-semibold text-white">Active Boundaries (2024)</div>
                <div className="mt-2 space-y-2">
                  {boundaries.map((b) => (
                    <div key={b.id} className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>{b.boundary_type} ({b.reporting_year})</span>
                      <Badge variant="success">Active</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Create Legal Entity */}
      <Modal
        isOpen={isEntityModalOpen}
        onClose={() => setIsEntityModalOpen(false)}
        title="Add Legal Entity to Organization"
      >
        <form onSubmit={handleCreateEntity} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Entity Name</label>
            <input
              type="text"
              required
              value={entityName}
              onChange={(e) => setEntityName(e.target.value)}
              placeholder="e.g. Nordic Solutions AB"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Entity Code</label>
              <input
                type="text"
                required
                value={entityCode}
                onChange={(e) => setEntityCode(e.target.value)}
                placeholder="ENT-NORD"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Country</label>
              <input
                type="text"
                required
                value={entityCountry}
                onChange={(e) => setEntityCountry(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Consolidation Method</label>
              <select
                value={consolidationMethod}
                onChange={(e) => setConsolidationMethod(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="Operational Control">Operational Control</option>
                <option value="Financial Control">Financial Control</option>
                <option value="Equity Share">Equity Share</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Ownership %</label>
              <input
                type="number"
                min={1}
                max={100}
                value={ownershipPct}
                onChange={(e) => setOwnershipPct(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsEntityModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Save Entity
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
