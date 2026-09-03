import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Download,
  FileText,
  CheckCircle2,
  Clock,
  Send,
  Building,
  Upload,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import api from '../../api/client';
import { ComplianceFramework, ComplianceDataPoint, CBAMRecord } from '../../types';
import { Badge } from '../../components/ui/Badge';
import { useAuthStore } from '../../store/authStore';

export const CompliancePage: React.FC = () => {
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [selectedFrameworkId, setSelectedFrameworkId] = useState<string>('');
  const [datapoints, setDatapoints] = useState<ComplianceDataPoint[]>([]);
  const [cbamRecords, setCbamRecords] = useState<CBAMRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'checklist' | 'cbam' | 'evidence'>('checklist');

  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();
  const canApprove = user?.role === 'Admin' || user?.role === 'Sustainability Manager' || user?.role === 'Auditor';

  useEffect(() => {
    fetchFrameworks();
    fetchCbamRecords();
  }, []);

  useEffect(() => {
    if (selectedFrameworkId) {
      fetchDatapoints(selectedFrameworkId);
    }
  }, [selectedFrameworkId]);

  const fetchFrameworks = async () => {
    try {
      const res = await api.get('/compliance/frameworks');
      setFrameworks(res.data);
      if (res.data.length) {
        setSelectedFrameworkId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load frameworks:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDatapoints = async (frameworkId: string) => {
    try {
      const res = await api.get(`/compliance/frameworks/${frameworkId}/datapoints`);
      setDatapoints(res.data);
    } catch (err) {
      console.error('Failed to load data points:', err);
    }
  };

  const fetchCbamRecords = async () => {
    try {
      const res = await api.get('/compliance/cbam');
      setCbamRecords(res.data);
    } catch (err) {
      console.error('Failed to load CBAM records:', err);
    }
  };

  const handleUpdateStatus = async (id: string, newStatus: string) => {
    try {
      await api.put(`/compliance/datapoints/${id}/status`, { status: newStatus });
      fetchDatapoints(selectedFrameworkId);
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleExportCsv = async () => {
    try {
      const response = await api.get(`/compliance/export/csv?framework_id=${selectedFrameworkId}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'decarbx_regulatory_disclosure.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export CSV:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  const selectedFramework = frameworks.find((f) => f.id === selectedFrameworkId);

  return (
    <div className="space-y-8">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Regulatory Compliance & Disclosure</h1>
          <p className="text-xs text-slate-400 mt-1">
            Standardized disclosures for CSRD / ESRS E1, CBAM, TCFD, EU Taxonomy, SEC Climate, and CDP with evidence verification.
          </p>
        </div>

        <button
          onClick={handleExportCsv}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 shadow-md transition-all self-start"
        >
          <Download className="w-4 h-4 text-emerald-400" />
          Export Disclosure CSV
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('checklist')}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'checklist'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Framework Disclosures Checklist
        </button>

        <button
          onClick={() => setActiveTab('cbam')}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'cbam'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Building className="w-4 h-4" />
          EU CBAM Quarterly Registry ({cbamRecords.length})
        </button>
      </div>

      {/* Tab: Framework Checklist */}
      {activeTab === 'checklist' && (
        <div className="space-y-6">
          {/* Framework Selector Pills */}
          <div className="flex flex-wrap gap-2">
            {frameworks.map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedFrameworkId(f.id)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  selectedFrameworkId === f.id
                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/40'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                }`}
              >
                {f.name}
              </button>
            ))}
          </div>

          {/* Framework Banner */}
          {selectedFramework && (
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-bold text-white text-sm">{selectedFramework.name}</div>
                <div className="text-xs text-slate-400 mt-0.5">{selectedFramework.description}</div>
              </div>
              <Badge variant="neutral">Jurisdiction: {selectedFramework.jurisdiction}</Badge>
            </div>
          )}

          {/* Data Points Table */}
          <div className="glass-panel p-6 rounded-2xl overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Requirement Code</th>
                  <th className="p-3">Disclosure Name</th>
                  <th className="p-3">Reported Value</th>
                  <th className="p-3">Linked Engine Source</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Approval Workflow</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 text-slate-300">
                {datapoints.map((dp) => (
                  <tr key={dp.id} className="hover:bg-slate-800/30">
                    <td className="p-3 font-mono font-bold text-emerald-400">{dp.code}</td>
                    <td className="p-3 font-medium text-white max-w-xs">{dp.name}</td>
                    <td className="p-3 font-semibold text-slate-200">
                      {dp.reported_value || <span className="text-slate-500 italic">Pending</span>}{' '}
                      {dp.unit && <span className="text-slate-400 text-[10px]">{dp.unit}</span>}
                    </td>
                    <td className="p-3 text-slate-400 text-[11px] truncate max-w-xs">
                      {dp.calculation_link || 'Direct Ledger Link'}
                    </td>
                    <td className="p-3">
                      <Badge
                        variant={
                          dp.status === 'approved' || dp.status === 'verified'
                            ? 'success'
                            : dp.status === 'in_review'
                            ? 'info'
                            : 'warning'
                        }
                      >
                        {dp.status}
                      </Badge>
                    </td>
                    <td className="p-3 text-right">
                      {canApprove && dp.status !== 'approved' ? (
                        <button
                          onClick={() => handleUpdateStatus(dp.id, 'approved')}
                          className="px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-700/60 text-emerald-400 hover:text-emerald-300 font-medium text-[11px] transition-colors"
                        >
                          Sign Off & Approve
                        </button>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Ready for Submission</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: CBAM Quarterly Registry */}
      {activeTab === 'cbam' && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div>
              <div className="font-bold text-white text-sm">EU Carbon Border Adjustment Mechanism (CBAM) Registry</div>
              <div className="text-xs text-slate-400 mt-0.5">
                Monitoring embedded direct and indirect GHG emissions for goods imported into the European customs territory.
              </div>
            </div>
            <Badge variant="scope1">EU Regulation 2023/956</Badge>
          </div>

          <div className="glass-panel p-6 rounded-2xl overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">CN Code</th>
                  <th className="p-3">Product Description</th>
                  <th className="p-3">Origin</th>
                  <th className="p-3">Quarter</th>
                  <th className="p-3">Import Mass</th>
                  <th className="p-3">Direct (t/t)</th>
                  <th className="p-3">Indirect (t/t)</th>
                  <th className="p-3 text-right">Total Embedded (tCO2e)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 text-slate-300">
                {cbamRecords.map((cb) => (
                  <tr key={cb.id} className="hover:bg-slate-800/30">
                    <td className="p-3 font-mono font-bold text-sky-400">{cb.product_code}</td>
                    <td className="p-3 font-medium text-white max-w-xs">{cb.product_description}</td>
                    <td className="p-3">📍 {cb.country_of_origin}</td>
                    <td className="p-3 font-mono text-slate-400">{cb.reporting_quarter}</td>
                    <td className="p-3 font-mono">{cb.imported_volume_tonnes.toLocaleString()} t</td>
                    <td className="p-3 font-mono">{cb.direct_embedded_emissions}</td>
                    <td className="p-3 font-mono">{cb.indirect_embedded_emissions}</td>
                    <td className="p-3 font-mono font-bold text-emerald-400 text-right">
                      {cb.total_embedded_emissions_tco2e.toLocaleString()} tCO2e
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
