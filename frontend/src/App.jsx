import React, { useState, useEffect } from 'react';
import { Shield, Sparkles, History, Upload, FileText, CheckCircle2, RefreshCw } from 'lucide-react';
import DragDropUpload from './components/DragDropUpload';
import AgentPipeline from './components/AgentPipeline';
import SummaryView from './components/SummaryView';
import RiskFactorsView from './components/RiskFactorsView';
import ChatSection from './components/ChatSection';
import LegalDisclaimer from './components/LegalDisclaimer';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  const [contractId, setContractId] = useState(null);
  const [contractFilename, setContractFilename] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  
  const [stepsState, setStepsState] = useState({
    classifier: { status: 'pending' },
    risk_analysis: { status: 'pending' },
    summary: { status: 'pending' },
    verifier: { status: 'pending' }
  });

  const [isPipelineCollapsed, setIsPipelineCollapsed] = useState(false);

  // Analysis outputs
  const [documentTitle, setDocumentTitle] = useState('');
  const [summaryText, setSummaryText] = useState('');
  const [clauses, setClauses] = useState([]);
  const [risks, setRisks] = useState([]);

  // Chat
  const [messages, setMessages] = useState([]);
  const [isChatSending, setIsChatSending] = useState(false);

  // History
  const [historyList, setHistoryList] = useState([]);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryList(data.contracts || []);
      }
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    setDocumentTitle('');
    setSummaryText('');
    setClauses([]);
    setRisks([]);
    setMessages([]);
    setIsPipelineCollapsed(false);
    setStepsState({
      classifier: { status: 'pending' },
      risk_analysis: { status: 'pending' },
      summary: { status: 'pending' },
      verifier: { status: 'pending' }
    });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Upload failed with status ${res.status}`);
      }

      const data = await res.json();
      setContractId(data.id);
      setContractFilename(data.filename);
      setDocumentTitle(data.title || data.filename);

      // Start Real SSE Pipeline Stream
      startAnalysisStream(data.id);
      fetchHistory();
    } catch (err) {
      alert(`Error uploading file: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const startAnalysisStream = (id) => {
    const eventSource = new EventSource(`${API_BASE}/analyze/${id}/stream`);

    // Keep-alive heartbeat listener
    eventSource.addEventListener('ping', () => {
      // Active connection confirmed
    });

    eventSource.addEventListener('step_start', (e) => {
      const data = JSON.parse(e.data);
      setStepsState((prev) => {
        // Keep completed if already completed in DB
        if (prev[data.step]?.status === 'completed') return prev;
        return {
          ...prev,
          [data.step]: { status: 'running' }
        };
      });
    });

    eventSource.addEventListener('step_finish', (e) => {
      const data = JSON.parse(e.data);
      setStepsState((prev) => ({
        ...prev,
        [data.step]: { status: 'completed', result: data.result }
      }));

      // Immediate display: if summary finishes, display title & summary right away
      if (data.step === 'summary' && data.result) {
        if (data.result.document_title) setDocumentTitle(data.result.document_title);
        if (data.result.summary) setSummaryText(data.result.summary);
      }

      // If risk finishes, update risks
      if (data.step === 'risk_analysis' && data.result) {
        setRisks(data.result);
      }

      fetchContractDetails(id);
    });

    eventSource.addEventListener('step_fail', (e) => {
      const data = JSON.parse(e.data);
      setStepsState((prev) => ({
        ...prev,
        [data.step]: { status: 'failed', error: data.error }
      }));
      eventSource.close();
    });

    eventSource.addEventListener('pipeline_complete', (e) => {
      setIsPipelineCollapsed(true);
      fetchContractDetails(id);
      eventSource.close();
    });

    eventSource.onerror = (e) => {
      console.warn('SSE stream error or complete:', e);
      eventSource.close();
    };
  };

  const fetchContractDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/contract/${id}`);
      if (res.ok) {
        const data = await res.json();
        if (data.clauses) setClauses(data.clauses);
        if (data.analysis) {
          if (data.analysis.document_title) setDocumentTitle(data.analysis.document_title);
          if (data.analysis.summary) setSummaryText(data.analysis.summary);
        }
        if (data.chat_history) setMessages(data.chat_history);
      }
    } catch (e) {
      console.error('Error fetching contract details:', e);
    }
  };

  const loadPastContract = async (pastContract) => {
    setContractId(pastContract.id);
    setContractFilename(pastContract.filename);
    setDocumentTitle(pastContract.title || pastContract.filename);
    setShowHistoryModal(false);
    setIsPipelineCollapsed(true);

    setStepsState({
      classifier: { status: 'completed' },
      risk_analysis: { status: 'completed' },
      summary: { status: 'completed' },
      verifier: { status: 'completed' }
    });

    await fetchContractDetails(pastContract.id);
  };

  const handleSendMessage = async (question) => {
    if (!contractId || !question.trim()) return;
    setIsChatSending(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: contractId,
          question: question
        })
      });

      if (!res.ok) throw new Error('Chat query failed');
      const data = await res.json();

      setMessages((prev) => [...prev, data]);
    } catch (e) {
      alert(`Chat error: ${e.message}`);
    } finally {
      setIsChatSending(false);
    }
  };

  const hasStartedPipeline = Boolean(contractId);
  const isSummaryReady = Boolean(summaryText);
  const isRisksReady = risks.length > 0 || clauses.some(c => c.risk_level);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#EF8557] to-[#f49e79] text-white flex items-center justify-center shadow-md shadow-[#EF8557]/20">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base sm:text-lg font-extrabold tracking-tight text-slate-900">
                Legal Contract Analyzer
              </h1>
              <p className="text-[11px] font-medium text-slate-500 hidden sm:block">
                Fully Offline • Privacy-First • Local Multi-Agent System
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Ollama (qwen2.5:3b + nomic)
            </div>

            <button
              onClick={() => {
                fetchHistory();
                setShowHistoryModal(true);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              <History className="w-4 h-4" />
              <span>History ({historyList.length})</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 flex flex-col">
        {!hasStartedPipeline ? (
          <div className="py-8 my-auto">
            <div className="text-center max-w-2xl mx-auto mb-8">
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#EF8557]/10 text-[#EF8557] border border-[#EF8557]/20 text-xs font-semibold mb-3">
                <Sparkles className="w-3.5 h-3.5 text-[#EF8557]" />
                Offline AI Legal Co-Counsel
              </span>
              <h2 className="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                Review Contracts with <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#EF8557] to-[#e47242]">Zero Privacy Risk</span>.
              </h2>
              <p className="text-base sm:text-lg text-slate-600 mt-3 max-w-xl mx-auto">
                Automatic clause segmentation, multi-agent classification, risk rating, and verified RAG Q&A running locally on your hardware.
              </p>
            </div>

            <DragDropUpload onUpload={handleUpload} isUploading={isUploading} />
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-white border border-slate-200/80 rounded-2xl p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 truncate max-w-xs sm:max-w-md">
                    {contractFilename}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {clauses.length} clauses indexed in ChromaDB
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  setContractId(null);
                  setIsPipelineCollapsed(false);
                }}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors inline-flex items-center gap-1"
              >
                <Upload className="w-3.5 h-3.5" />
                New Document
              </button>
            </div>

            <AgentPipeline
              stepsState={stepsState}
              onRetry={(stepKey) => startAnalysisStream(contractId)}
              isCollapsed={isPipelineCollapsed}
              onToggleCollapse={() => setIsPipelineCollapsed(!isPipelineCollapsed)}
            />

            {/* Results Section */}
            {isSummaryReady && (
              <SummaryView
                title={documentTitle}
                summary={summaryText}
              />
            )}

            {isRisksReady && (
              <RiskFactorsView
                clauses={clauses}
                risks={risks.length > 0 ? risks : clauses.map(c => ({
                  clause_id: c.id,
                  risk_level: c.risk_level || 'Low',
                  reason: c.risk_reason || 'Standard contractual term.'
                }))}
              />
            )}

            {hasStartedPipeline && (
              <ChatSection
                contractId={contractId}
                messages={messages}
                onSendMessage={handleSendMessage}
                isSending={isChatSending}
              />
            )}
          </div>
        )}

        <LegalDisclaimer />
      </main>

      {/* History Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <History className="w-5 h-5 text-blue-600" />
                Contract History
              </h3>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 max-h-80 overflow-y-auto space-y-2">
              {historyList.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">
                  No contracts analyzed yet. Upload your first PDF to begin!
                </p>
              ) : (
                historyList.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => loadPastContract(item)}
                    className="p-3.5 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                        {item.title || item.filename}
                      </h4>
                      <p className="text-xs text-slate-500">
                        {item.clause_count} clauses • {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="text-xs font-semibold text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                      Open →
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
