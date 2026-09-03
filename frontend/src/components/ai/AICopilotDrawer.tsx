import React, { useState } from 'react';
import {
  Bot,
  Sparkles,
  X,
  Send,
  CheckCircle2,
  TrendingDown,
  ShieldCheck,
  DollarSign,
  ChevronRight,
  Lightbulb,
} from 'lucide-react';
import api from '../../api/client';
import { Badge } from '../ui/Badge';

export const AICopilotDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<any[]>([
    {
      role: 'assistant',
      topic: 'Welcome to DecarbX Environmental Intelligence',
      summary: 'I am your audit-grade AI decarbonization copilot. I have real-time access to your Scope 1, 2, and 3 actuals, supplier scores, PCF lifecycle models, and regulatory compliance status.',
      key_findings: [
        'Total Gross Emissions: 4,873.3 tCO2e (-59.1% vs 2021 base year).',
        'Scope 3 accounts for 82.9% of total footprint, concentrated in Tier 1 suppliers.',
        'SBTi 2030 near-term trajectory is currently ahead of glidepath.'
      ],
      recommended_actions: [
        'Click any prompt pill below or enter a custom query to analyze your carbon ledger.'
      ]
    }
  ]);

  const quickPrompts = [
    { label: 'Scope 3 & Supplier Hotspots', query: 'Analyze our Scope 3 emissions hotspots and supplier contributors' },
    { label: 'SBTi 1.5°C Alignment', query: 'Are we on track for our SBTi 2030 reduction target?' },
    { label: 'CSRD & CBAM Readiness', query: 'Summarize our CSRD ESRS E1 and CBAM compliance status' },
    { label: 'Carbon Shadow Pricing & ROI', query: 'What is our financial liability at $65/tCO2e internal carbon price?' },
  ];

  const handleSendPrompt = async (queryText: string) => {
    const q = queryText || prompt;
    if (!q.trim()) return;

    // Append user message
    setChatHistory((prev) => [...prev, { role: 'user', content: q }]);
    setPrompt('');
    setLoading(true);

    try {
      const res = await api.post('/analytics/ai/copilot-chat', { prompt: q });
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          topic: res.data.topic,
          summary: res.data.summary,
          key_findings: res.data.key_findings,
          recommended_actions: res.data.recommended_actions,
        },
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          topic: 'Analysis Error',
          summary: 'Failed to synthesize ledger data. Please verify backend connectivity.',
          key_findings: [],
          recommended_actions: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-2xl shadow-emerald-950/80 border border-emerald-400/40 transition-all hover:scale-105"
        >
          <div className="relative">
            <Bot className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-200"></span>
            </span>
          </div>
          <span>DecarbX AI Copilot</span>
          <Badge variant="success">Online</Badge>
        </button>
      )}

      {/* Slide-out Drawer */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[520px] bg-slate-950/95 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col transition-all">
          {/* Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-950/80 border border-emerald-500/50 flex items-center justify-center text-emerald-400">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <div className="font-bold text-white text-sm flex items-center gap-2">
                  DecarbX AI Copilot
                  <Badge variant="success">Environmental Intelligence</Badge>
                </div>
                <div className="text-[11px] text-slate-400">Grounded in verified Scope 1-3 ledger actuals</div>
              </div>
            </div>

            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Prompt Chips */}
          <div className="p-3 border-b border-slate-800/80 bg-slate-900/30 flex items-center gap-1.5 overflow-x-auto text-[11px]">
            {quickPrompts.map((qp, idx) => (
              <button
                key={idx}
                onClick={() => handleSendPrompt(qp.query)}
                className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-emerald-300 transition-colors"
              >
                {qp.label}
              </button>
            ))}
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {chatHistory.map((msg, i) => (
              <div key={i} className="space-y-2">
                {msg.role === 'user' ? (
                  <div className="flex justify-end">
                    <div className="bg-emerald-700/80 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[85%] font-medium">
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 text-slate-300">
                    <div className="flex items-center gap-2 font-bold text-emerald-400 text-xs">
                      <Bot className="w-4 h-4" />
                      {msg.topic}
                    </div>

                    <div className="text-slate-200 leading-relaxed font-sans text-xs">
                      {msg.summary}
                    </div>

                    {msg.key_findings && msg.key_findings.length > 0 && (
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-850 space-y-1.5">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          Key Intelligence Findings
                        </span>
                        <ul className="space-y-1">
                          {msg.key_findings.map((f: string, fIdx: number) => (
                            <li key={fIdx} className="flex items-start gap-1.5 text-[11px] text-slate-300">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <span>{f}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {msg.recommended_actions && msg.recommended_actions.length > 0 && (
                      <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30 space-y-1.5">
                        <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                          <Lightbulb className="w-3.5 h-3.5" />
                          Recommended Interventions
                        </span>
                        <ul className="space-y-1">
                          {msg.recommended_actions.map((a: string, aIdx: number) => (
                            <li key={aIdx} className="flex items-start gap-1.5 text-[11px] text-slate-200">
                              <ChevronRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <span>{a}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-3 text-slate-400 text-xs">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-emerald-500 border-t-transparent"></div>
                <span>Synthesizing carbon ledger & calculating emissions impacts...</span>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-3.5 border-t border-slate-800 bg-slate-900/80">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendPrompt(prompt);
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask DecarbX AI about emissions, roadmaps, or CSRD..."
                className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
              <button
                type="submit"
                disabled={loading || !prompt.trim()}
                className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
