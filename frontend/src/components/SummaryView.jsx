import React from 'react';
import { FileText, Sparkles, CheckCircle2 } from 'lucide-react';

export default function SummaryView({ title, summary }) {
  if (!summary) return null;

  return (
    <div className="w-full max-w-4xl mx-auto my-8 animate-fadeIn">
      <div className="bg-white border border-slate-200/90 rounded-3xl p-6 sm:p-8 shadow-sm hover:shadow-md transition-all">
        {/* Document Title Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2">
              <FileText className="w-3.5 h-3.5" />
              Document Analysis
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {title || 'Contract Agreement'}
            </h2>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-center">
            <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Summary Ready
            </span>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="mt-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-500" />
            Plain English Executive Summary
          </h3>
          <div className="bg-slate-50/70 border border-slate-200/70 rounded-2xl p-5 sm:p-6 text-slate-700 leading-relaxed text-base sm:text-lg">
            {summary}
          </div>
        </div>
      </div>
    </div>
  );
}
