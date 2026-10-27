import React from 'react';
import { CheckCircle2, XCircle, RotateCcw, Sparkles, ShieldCheck, Tag, AlertTriangle, FileText, ChevronDown, ChevronUp } from 'lucide-react';

const STEP_METADATA = [
  {
    key: 'classifier',
    name: 'Classifier',
    desc: 'Categorizes clauses into payment, termination, penalty, auto-renewal, non-compete, etc.',
    icon: Tag,
  },
  {
    key: 'risk_analysis',
    name: 'Risk Analysis',
    desc: 'Rates liability risk (Low/Medium/High) with clear one-line justifications.',
    icon: AlertTriangle,
  },
  {
    key: 'summary',
    name: 'Summary',
    desc: 'Extracts official document title and explains terms in simple English.',
    icon: FileText,
  },
  {
    key: 'verifier',
    name: 'Verifier',
    desc: 'Strictly audits outputs against raw contract text for verified citations.',
    icon: ShieldCheck,
  },
];

export default function AgentPipeline({ stepsState, onRetry, isCollapsed, onToggleCollapse }) {
  const isAllFinished = STEP_METADATA.every((s) => stepsState[s.key]?.status === 'completed');

  // Collapsed compact progress bar mode
  if (isCollapsed) {
    return (
      <div className="w-full max-w-3xl mx-auto my-6 transition-all duration-500">
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200/80 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-800">
                  Multi-Agent Pipeline Complete
                </h4>
                <p className="text-xs text-slate-500">
                  4/4 agents executed and verified offline
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2">
                {STEP_METADATA.map((s) => (
                  <span
                    key={s.key}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-medium rounded-full border border-emerald-200"
                  >
                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    {s.name}
                  </span>
                ))}
              </div>
              <button
                onClick={onToggleCollapse}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                Expand Pipeline
                <ChevronDown className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Expanded vertical pipeline
  return (
    <div className="w-full max-w-2xl mx-auto my-10 transition-all duration-500">
      <div className="bg-white border border-slate-200/90 rounded-3xl p-6 sm:p-8 shadow-xl shadow-slate-200/50">
        <div className="flex items-center justify-between pb-6 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              LangGraph Agent Pipeline
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Live Server-Sent Events stream from local Ollama agents
            </p>
          </div>
          {isAllFinished && (
            <button
              onClick={onToggleCollapse}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              Minimize
              <ChevronUp className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="mt-8 space-y-2 relative">
          {STEP_METADATA.map((step, idx) => {
            const current = stepsState[step.key] || { status: 'pending' };
            const isCompleted = current.status === 'completed';
            const isRunning = current.status === 'running';
            const isFailed = current.status === 'failed';
            const isPending = current.status === 'pending';
            const isLast = idx === STEP_METADATA.length - 1;
            const Icon = step.icon;

            return (
              <div key={step.key} className="relative flex items-start gap-4">
                {/* Connecting Line */}
                {!isLast && (
                  <div className="absolute left-6 top-12 bottom-0 w-0.5 -ml-[1px] z-0">
                    <div
                      className={`h-full transition-all duration-700 ease-out ${
                        isCompleted
                          ? 'bg-emerald-500 w-0.5'
                          : isRunning
                          ? 'bg-blue-300 w-0.5'
                          : 'bg-slate-200 w-0.5'
                      }`}
                    />
                  </div>
                )}

                {/* Step Node Icon / Status Indicator */}
                <div className="relative z-10 flex-shrink-0">
                  {isCompleted ? (
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/20 transform scale-100 transition-all duration-300">
                      <CheckCircle2 className="w-6 h-6 stroke-[2.5]" />
                    </div>
                  ) : isRunning ? (
                    <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center shadow-lg shadow-blue-500/30 animate-pulse-glow">
                      <div className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-dot-1"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-dot-2"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-dot-3"></span>
                      </div>
                    </div>
                  ) : isFailed ? (
                    <div className="w-12 h-12 rounded-2xl bg-red-500 text-white flex items-center justify-center shadow-md shadow-red-500/20">
                      <XCircle className="w-6 h-6 stroke-[2.5]" />
                    </div>
                  ) : (
                    <div className="w-12 h-12 rounded-2xl bg-slate-100 border border-slate-200 text-slate-400 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-slate-400" />
                    </div>
                  )}
                </div>

                {/* Step Content */}
                <div className="flex-1 pt-1.5 pb-8">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                        0{idx + 1}
                      </span>
                      <h4
                        className={`text-base font-bold tracking-tight transition-colors ${
                          isRunning
                            ? 'text-blue-600'
                            : isCompleted
                            ? 'text-slate-900'
                            : isFailed
                            ? 'text-red-600'
                            : 'text-slate-400'
                        }`}
                      >
                        {step.name}
                      </h4>
                    </div>

                    {/* Status Badges */}
                    {isRunning && (
                      <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-600 rounded-full border border-blue-200 animate-pulse">
                        Analyzing...
                      </span>
                    )}
                    {isCompleted && (
                      <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
                        Verified
                      </span>
                    )}
                    {isFailed && (
                      <button
                        onClick={() => onRetry(step.key)}
                        className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
                      >
                        <RotateCcw className="w-3 h-3" />
                        Retry
                      </button>
                    )}
                  </div>

                  <p className="text-xs sm:text-sm text-slate-500 mt-1">
                    {step.desc}
                  </p>

                  {/* Failure message if any */}
                  {isFailed && current.error && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 p-2.5 rounded-lg border border-red-200">
                      {current.error}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
