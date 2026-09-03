import React, { useEffect, useState } from 'react';
import {
  Layers,
  Plus,
  FileSpreadsheet,
  CheckCircle2,
  Box,
  Truck,
  RotateCcw,
  Zap,
  Printer,
  ChevronRight,
  Split,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import api from '../../api/client';
import { ProductItem } from '../../types';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { useAuthStore } from '../../store/authStore';

export const PCFPage: React.FC = () => {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [pcfResult, setPcfResult] = useState<any>(null);
  const [compareItems, setCompareItems] = useState<any[]>([]);
  
  // Boundary selection
  const [boundary, setBoundary] = useState<'cradle-to-gate' | 'gate-to-gate' | 'cradle-to-grave'>('cradle-to-gate');
  const [allocationMethod, setAllocationMethod] = useState('Mass Allocation');

  const [loading, setLoading] = useState(true);
  const [isIsoModalOpen, setIsIsoModalOpen] = useState(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);

  const { user } = useAuthStore();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const res = await api.get('/pcf/products');
      setProducts(res.data);
      if (res.data.length) {
        fetchProductDetail(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProductDetail = async (id: string) => {
    try {
      const res = await api.get(`/pcf/products/${id}`);
      setSelectedProduct(res.data);
      // Run PCF calculation
      calculatePcf(id, boundary);
    } catch (err) {
      console.error('Failed to load product detail:', err);
    }
  };

  const calculatePcf = async (productId: string, selectedBoundary: string) => {
    try {
      const res = await api.post('/pcf/calculate', {
        product_id: productId,
        boundary: selectedBoundary,
        allocation_method: allocationMethod,
        use_phase_kwh_per_year: 45.0,
        lifespan_years: 3.0,
        recycling_rate_pct: 85.0,
      });
      setPcfResult(res.data);
    } catch (err) {
      console.error('Failed to calculate PCF:', err);
    }
  };

  const handleBoundaryChange = (newBoundary: any) => {
    setBoundary(newBoundary);
    if (selectedProduct) {
      calculatePcf(selectedProduct.product.id, newBoundary);
    }
  };

  const handleCompareAll = async () => {
    if (products.length < 2) return;
    try {
      const ids = products.slice(0, 4).map((p) => `product_ids=${p.id}`).join('&');
      const res = await api.get(`/pcf/compare?${ids}`);
      setCompareItems(res.data);
      setIsCompareModalOpen(true);
    } catch (err) {
      console.error('Failed to load comparison:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  const stageChartData = pcfResult?.stage_breakdown
    ? [
        { stage: 'Raw Materials', emissions: pcfResult.stage_breakdown.raw_materials },
        { stage: 'Manufacturing', emissions: pcfResult.stage_breakdown.manufacturing },
        { stage: 'Packaging', emissions: pcfResult.stage_breakdown.packaging },
        { stage: 'Logistics', emissions: pcfResult.stage_breakdown.logistics },
        { stage: 'Use Phase', emissions: pcfResult.stage_breakdown.use_phase },
        { stage: 'End of Life', emissions: pcfResult.stage_breakdown.end_of_life },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Product LCA & Carbon Footprint (PCF)</h1>
          <p className="text-xs text-slate-400 mt-1">
            ISO 14067:2018 aligned lifecycle assessment with multi-level Bill of Materials and cradle-to-grave process modeling.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCompareAll}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
          >
            <Split className="w-4 h-4 text-sky-400" />
            Compare SKUs
          </button>
          <button
            onClick={() => setIsIsoModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950 transition-all"
          >
            <FileSpreadsheet className="w-4 h-4" />
            ISO 14067 Report
          </button>
        </div>
      </div>

      {/* Main Grid: SKU selector list on left, PCF Modeling view on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: SKU Registry */}
        <div className="glass-panel p-5 rounded-2xl space-y-3">
          <h2 className="text-sm font-bold text-white tracking-wide uppercase tracking-wider mb-2">
            Registered Products & SKUs
          </h2>
          <div className="space-y-2">
            {products.map((p) => (
              <div
                key={p.id}
                onClick={() => fetchProductDetail(p.id)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  selectedProduct?.product.id === p.id
                    ? 'border-emerald-500/80 bg-emerald-950/30 shadow-md'
                    : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{p.name}</span>
                  <Badge variant="neutral">{p.functional_unit}</Badge>
                </div>
                <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
                  <span className="font-mono text-emerald-400">{p.sku}</span>
                  <span>{p.unit_weight_kg} kg weight</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: PCF Details & Stage Breakdown */}
        <div className="lg:col-span-2 space-y-6">
          {selectedProduct && pcfResult && (
            <>
              {/* Product Header & Boundary Switcher */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedProduct.product.name}</h2>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      <span>SKU: <strong className="text-slate-200">{selectedProduct.product.sku}</strong></span>
                      <span>Functional Unit: <strong className="text-emerald-400">{selectedProduct.product.functional_unit}</strong></span>
                    </div>
                  </div>

                  {/* Footprint Hero Stat */}
                  <div className="p-3 rounded-xl bg-slate-950 border border-emerald-500/40 text-right">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Total PCF</div>
                    <div className="text-2xl font-black text-emerald-400 font-mono">
                      {pcfResult.total_pcf_kgco2e} <span className="text-xs font-normal text-slate-400">kgCO2e</span>
                    </div>
                  </div>
                </div>

                {/* Boundary Radio Buttons */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <span className="text-slate-400 font-semibold">Assessment Boundary:</span>
                  <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-xl border border-slate-800">
                    {(['cradle-to-gate', 'gate-to-gate', 'cradle-to-grave'] as const).map((b) => (
                      <button
                        key={b}
                        onClick={() => handleBoundaryChange(b)}
                        className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                          boundary === b
                            ? 'bg-emerald-600 text-white shadow-sm'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        {b.replace('-', ' ').replace('-', ' ').toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Lifecycle Stage Emissions Bar Chart */}
              <div className="glass-panel p-6 rounded-2xl">
                <h3 className="text-sm font-bold text-white mb-4">Emissions by Lifecycle Stage (kgCO2e per unit)</h3>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stageChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="stage" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                      <Bar dataKey="emissions" name="kgCO2e" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Bill of Materials (BOM) & Process Details */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white">Bill of Materials (BOM) Component Breakdown</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                      <tr>
                        <th className="p-2.5">Component</th>
                        <th className="p-2.5">Material</th>
                        <th className="p-2.5">Mass (kg)</th>
                        <th className="p-2.5">Scrap %</th>
                        <th className="p-2.5">Factor</th>
                        <th className="p-2.5 text-right">Emissions (kgCO2e)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {pcfResult.bom_breakdown?.map((item: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-2.5 font-medium text-white">{item.component}</td>
                          <td className="p-2.5">{item.material}</td>
                          <td className="p-2.5 font-mono">{item.quantity_kg}</td>
                          <td className="p-2.5 font-mono">{item.scrap_rate_pct}%</td>
                          <td className="p-2.5 font-mono text-slate-400">{item.factor_kgco2e_per_kg}</td>
                          <td className="p-2.5 font-mono font-bold text-emerald-400 text-right">{item.emissions_kgco2e}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Modal: ISO 14067 Export Report */}
      <Modal
        isOpen={isIsoModalOpen}
        onClose={() => setIsIsoModalOpen(false)}
        title="ISO 14067:2018 Product Carbon Footprint Declaration"
        maxWidth="2xl"
      >
        {pcfResult && (
          <div className="space-y-6 text-xs print:p-0">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-bold text-white text-sm">Verification Standard: ISO 14067:2018</div>
                <div className="text-slate-400 mt-0.5">Greenhouse gases — Carbon footprint of products</div>
              </div>
              <Badge variant="success">Audit-Ready Report</Badge>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-slate-400">Product Name & SKU</span>
                <div className="text-white font-semibold">{pcfResult.product_name} ({pcfResult.product_sku})</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-slate-400">Declared Functional Unit</span>
                <div className="text-emerald-400 font-semibold">{pcfResult.functional_unit}</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-center space-y-1">
              <div className="text-xs text-slate-400 uppercase font-semibold">Total Product Carbon Footprint</div>
              <div className="text-3xl font-extrabold text-emerald-400 font-mono">
                {pcfResult.total_pcf_kgco2e} kgCO2e
              </div>
              <div className="text-[11px] text-slate-400">Boundary: {pcfResult.boundary} • Allocation: {pcfResult.allocation_method}</div>
            </div>

            <div className="space-y-2">
              <span className="font-semibold text-white">Stage-by-Stage Breakdown:</span>
              <div className="grid grid-cols-3 gap-2 text-center">
                {Object.entries(pcfResult.stage_breakdown || {}).map(([stage, val]: any) => (
                  <div key={stage} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">{stage.replace('_', ' ')}</div>
                    <div className="font-mono font-bold text-white mt-0.5">{val} kg</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
              <button
                onClick={() => window.print()}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium"
              >
                <Printer className="w-4 h-4" />
                Print / Save PDF
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal: SKU Comparison View */}
      <Modal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        title="SKU-Level PCF Comparative Assessment"
        maxWidth="2xl"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-400">Side-by-side comparative analysis of carbon intensity across product portfolio.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {compareItems.map((item) => (
              <div key={item.product_id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-center">
                <div className="font-bold text-white truncate">{item.name}</div>
                <div className="text-[10px] text-slate-400 font-mono">{item.sku}</div>
                <div className="text-lg font-black text-emerald-400 font-mono">
                  {item.total_pcf_kgco2e} <span className="text-[10px] font-normal text-slate-400">kg</span>
                </div>
                <Badge variant="neutral">{item.boundary}</Badge>
              </div>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  );
};
