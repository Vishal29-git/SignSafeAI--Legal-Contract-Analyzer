import React, { useState } from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle2, ChevronDown, ChevronUp, Shield, Filter } from 'lucide-react';

export default function RiskFactorsView({ clauses, risks }) {
  const [filter, setFilter] = useState('ALL'); // ALL, High, Medium, Low
  const [expandedClauses, setExpandedClauses] = useState({});

  if (!risks || risks.length === 0) return null;

  // Build a lookup map from clauses by ID
  const clauseMap = {};
  (clauses || []).forEach((c) => {
    clauseMap[c.id] = c;
  });

  const toggleExpand = (id) => {
    setExpandedClauses((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const filteredRisks = risks.filter((r) => {
    if (filter === 'ALL') return true;
    return r.risk_level.toLowerCase() === filter.toLowerCase();
  });

  const highCount = risks.filter((r) => r.risk_level === 'High').length;
  const medCount = risks.filter((r) => r.risk_level === 'Medium').length;
  const lowCount = risks.filter((r) => r.risk_level === 'Low').length;

  return (
    <div className="w-full max-w-4xl mx-auto my-10 animate-fadeIn">
      {/* Section Header & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold mb-1">
            <Shield className="w-3.5 h-3.5" />
            Risk Assessment
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Key Risk Factors & Liabilities
          </h2>
          <p className="text-sm text-slate-500">
            Clauses rated by liability exposure with underlying legal source text
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl self-start sm:self-center">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === 'ALL'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All ({risks.length})
          </button>
          <button
            onClick={() => setFilter('High')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === 'High'
                ? 'bg-red-500 text-white shadow-sm'
                : 'text-red-700 hover:bg-red-50'
            }`}
          >
            High ({highCount})
          </button>
          <button
            onClick={() => setFilter('Medium')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === 'Medium'
                ? 'bg-amber-500 text-white shadow-sm'
                : 'text-amber-700 hover:bg-amber-50'
            }`}
          >
            Medium ({medCount})
          </button>
          <button
            onClick={() => setFilter('Low')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === 'Low'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-700 hover:bg-emerald-50'
            }`}
          >
            Low ({lowCount})
          </button>
        </div>
      </div>

      {/* Risk Cards Grid / List */}
      <div className="space-y-4">
        {filteredRisks.map((riskItem, idx) => {
          const clause = clauseMap[riskItem.clause_id] || {};
          const isHigh = riskItem.risk_level === 'High';
          const isMedium = riskItem.risk_level === 'Medium';
          const isLow = riskItem.risk_level === 'Low';
          const isExpanded = expandedClauses[riskItem.clause_id] ?? (isHigh || isMedium);

          let cardBorder = 'border-emerald-200 bg-emerald-50/20';
          let badgeBg = 'bg-emerald-100 text-emerald-800 border-emerald-300';
          let icon = <CheckCircle2 className="w-5 h-5 text-emerald-600" />;
          let barBg = 'bg-emerald-500';

          if (isHigh) {
            cardBorder = 'border-red-200 bg-red-50/30';
            badgeBg = 'bg-red-100 text-red-800 border-red-300';
            icon = <AlertOctagon className="w-5 h-5 text-red-600" />;
            barBg = 'bg-red-500';
          } else if (isMedium) {
            cardBorder = 'border-amber-200 bg-amber-50/30';
            badgeBg = 'bg-amber-100 text-amber-800 border-amber-300';
            icon = <AlertTriangle className="w-5 h-5 text-amber-600" />;
            barBg = 'bg-amber-500';
          }

          return (
            <div
              key={idx}
              className={`rounded-2xl border ${cardBorder} p-5 sm:p-6 bg-white shadow-sm hover:shadow-md transition-all relative overflow-hidden`}
            >
              {/* Colored Side Bar Accent */}
              <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${barBg}`} />

              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-white shadow-sm border border-slate-100 flex-shrink-0">
                    {icon}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono font-bold text-slate-500">
                        {clause.clause_number || `Clause ${idx + 1}`}
                      </span>
                      <h4 className="text-base font-bold text-slate-900">
                        {clause.heading || 'Contract Provision'}
                      </h4>
                      {clause.clause_type && (
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 capitalize">
                          {clause.clause_type}
                        </span>
                      )}
                    </div>
                    {/* Reason */}
                    <p className="text-sm font-medium text-slate-700 mt-2">
                      <span className="font-semibold text-slate-900">Risk Assessment: </span>
                      {riskItem.reason}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <span className={`inline-flex items-center text-xs font-bold px-3 py-1 rounded-full border ${badgeBg}`}>
                    {riskItem.risk_level} Risk
                  </span>
                </div>
              </div>

              {/* Source Clause Underneath */}
              <div className="mt-4 pt-3 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => toggleExpand(riskItem.clause_id)}
                    className="text-xs font-semibold text-slate-500 hover:text-slate-800 inline-flex items-center gap-1 transition-colors"
                  >
                    <span>Source Clause Text</span>
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </button>
                  {clause.page_number && (
                    <span className="text-xs text-slate-400">
                      Page {clause.page_number}
                    </span>
                  )}
                </div>

                {isExpanded && (
                  <div className="mt-2.5 bg-slate-50 rounded-xl p-3.5 text-xs sm:text-sm font-mono text-slate-700 leading-relaxed border border-slate-200/80 whitespace-pre-wrap">
                    {clause.text || 'No explicit clause text recorded.'}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
