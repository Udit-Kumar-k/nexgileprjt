import React, { useEffect, useState } from 'react';
import {
  Cable,
  Upload,
  RefreshCw,
  Download,
  CheckCircle2,
  AlertCircle,
  Clock,
  Terminal,
  FileSpreadsheet,
} from 'lucide-react';
import api from '../../api/client';
import { ConnectorConfig, WebhookLog } from '../../types';
import { Badge } from '../../components/ui/Badge';
import { useAuthStore } from '../../store/authStore';

export const IntegrationPage: React.FC = () => {
  const [connectors, setConnectors] = useState<ConnectorConfig[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookLog[]>([]);
  const [entities, setEntities] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);

  // CSV file upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadEntityId, setUploadEntityId] = useState<string>('');
  const [uploadFacilityId, setUploadFacilityId] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();

  useEffect(() => {
    fetchIntegrationData();
    fetchOrgReferences();
  }, []);

  const fetchIntegrationData = async () => {
    try {
      const [cRes, wRes] = await Promise.all([
        api.get('/integration/connectors'),
        api.get('/integration/webhooks'),
      ]);
      setConnectors(cRes.data);
      setWebhooks(wRes.data);
    } catch (err) {
      console.error('Failed to load integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrgReferences = async () => {
    try {
      const [entRes, facRes] = await Promise.all([
        api.get('/organization/entities'),
        api.get('/organization/facilities'),
      ]);
      setEntities(entRes.data);
      setFacilities(facRes.data);
      if (entRes.data.length) setUploadEntityId(entRes.data[0].id);
      if (facRes.data.length) setUploadFacilityId(facRes.data[0].id);
    } catch (err) {
      console.error('Failed to load org refs:', err);
    }
  };

  const handleSyncConnector = async (id: string) => {
    try {
      await api.post(`/integration/connectors/${id}/sync`);
      fetchIntegrationData();
    } catch (err) {
      console.error('Failed to sync connector:', err);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/integration/template-csv', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'decarbx_activity_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download template:', err);
    }
  };

  const handleUploadCsv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !uploadEntityId || !uploadFacilityId) return;

    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('organization_id', user?.organization_id || 'default-org');
    formData.append('entity_id', uploadEntityId);
    formData.append('facility_id', uploadFacilityId);

    try {
      const res = await api.post('/integration/upload-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadResult({
        success: true,
        imported_count: res.data.imported_count,
        failed_count: res.data.failed_count,
        errors: res.data.errors,
      });
      setSelectedFile(null);
    } catch (err: any) {
      setUploadResult({
        success: false,
        error: err.response?.data?.detail || 'CSV upload failed.',
      });
    } finally {
      setUploading(false);
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
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Integrations & Data Connectors</h1>
        <p className="text-xs text-slate-400 mt-1">
          Monitor enterprise system connectors (ERP, utility bill EDI, smart meters), upload bulk activity CSV files, and inspect inbound webhook payloads.
        </p>
      </div>

      {/* Row 1: Working Manual CSV Activity Ingestion Wizard */}
      <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              Manual CSV Activity Data Ingestion (Live Processing)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Upload multi-facility Scope 1, 2, and 3 activity files. Calculations and audit formula lineage are computed automatically.
            </p>
          </div>

          <button
            onClick={handleDownloadTemplate}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all self-start"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            Download Sample CSV Template
          </button>
        </div>

        {uploadResult && (
          <div
            className={`p-4 rounded-xl text-xs border ${
              uploadResult.success
                ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                : 'bg-rose-950/40 border-rose-800/80 text-rose-300'
            }`}
          >
            {uploadResult.success ? (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Successfully ingested <strong>{uploadResult.imported_count}</strong> activity records and computed deterministic emission records!
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{uploadResult.error}</span>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleUploadCsv} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Entity</label>
            <select
              value={uploadEntityId}
              onChange={(e) => setUploadEntityId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            >
              {entities.map((ent) => (
                <option key={ent.id} value={ent.id}>{ent.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Facility</label>
            <select
              value={uploadFacilityId}
              onChange={(e) => setUploadFacilityId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            >
              {facilities.map((fac) => (
                <option key={fac.id} value={fac.id}>{fac.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Select CSV File</label>
            <input
              type="file"
              accept=".csv"
              required
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-white hover:file:bg-slate-700 cursor-pointer"
            />
          </div>

          <button
            type="submit"
            disabled={uploading || !selectedFile}
            className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center justify-center gap-2 shadow-md shadow-emerald-950 disabled:opacity-50 transition-all"
          >
            <Upload className="w-4 h-4" />
            {uploading ? 'Processing File...' : 'Upload & Compute'}
          </button>
        </form>
      </div>

      {/* Row 2: Configured Enterprise Connectors Hub */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Cable className="w-4 h-4 text-emerald-400" />
          Enterprise Connectors Status ({connectors.length})
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {connectors.map((c) => (
            <div key={c.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-xs">{c.name}</span>
                <Badge variant={c.status === 'active' ? 'success' : 'danger'}>{c.status}</Badge>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Type: <strong className="text-slate-300">{c.connector_type}</strong></span>
                <span className="font-mono text-emerald-400">{c.records_synced.toLocaleString()} records synced</span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-850">
                <span>Frequency: {c.sync_frequency}</span>
                <button
                  onClick={() => handleSyncConnector(c.id)}
                  className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-medium"
                >
                  <RefreshCw className="w-3 h-3" />
                  Sync Now
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Row 3: Inbound Webhook Event Log Viewer */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          Inbound Webhook Live Stream ({webhooks.length})
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Event Type</th>
                <th className="p-3">Inbound Source</th>
                <th className="p-3">Status</th>
                <th className="p-3">Payload Preview</th>
                <th className="p-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70 text-slate-300 font-mono text-[11px]">
              {webhooks.map((w) => (
                <tr key={w.id} className="hover:bg-slate-800/30">
                  <td className="p-3 font-semibold text-emerald-400">{w.event_type}</td>
                  <td className="p-3 text-slate-300 font-sans">{w.source}</td>
                  <td className="p-3 font-sans">
                    <Badge variant={w.status === 'success' ? 'success' : 'danger'}>{w.status}</Badge>
                  </td>
                  <td className="p-3 text-slate-400 max-w-xs truncate">{w.payload_preview}</td>
                  <td className="p-3 text-slate-500 text-right font-sans">{w.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
