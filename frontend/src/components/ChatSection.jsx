import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, ShieldCheck, FileText, ChevronDown, ChevronUp, Bot, Sparkles } from 'lucide-react';

export default function ChatSection({ contractId, messages, onSendMessage, isSending }) {
  const [inputQuestion, setInputQuestion] = useState('');
  const [expandedSources, setExpandedSources] = useState({});
  const chatEndRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuestion.trim() || isSending) return;
    onSendMessage(inputQuestion.trim());
    setInputQuestion('');
  };

  const toggleSource = (idx) => {
    setExpandedSources((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  useEffect(() => {
    if (messages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isSending]);

  return (
    <div className="w-full max-w-4xl mx-auto my-12 pb-32 animate-fadeIn">
      {/* Section Header */}
      <div className="mb-6">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-1">
          <MessageSquare className="w-3.5 h-3.5" />
          Verified RAG Q&A
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Contract Inquiry Assistant
        </h2>
        <p className="text-sm text-slate-500">
          Ask any specific question about this contract. Answers are strictly verified against source clauses.
        </p>
      </div>

      {/* Suggested Questions */}
      {messages.length === 0 && (
        <div className="mb-8 p-6 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-amber-500" />
            Suggested Quick Inquiries
          </p>
          <div className="flex flex-wrap gap-2">
            {[
              "What is the penalty for breach of confidentiality?",
              "What is the contract term and termination notice period?",
              "What is the governing law and jurisdiction?",
              "Are there any automatic renewal clauses?"
            ].map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onSendMessage(q)}
                className="text-xs font-medium px-3.5 py-2 bg-slate-50 hover:bg-blue-50 text-slate-700 hover:text-blue-700 rounded-xl border border-slate-200/80 hover:border-blue-200 transition-all text-left"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message History */}
      <div className="space-y-6">
        {messages.map((item, idx) => {
          const isVerified = item.verified !== false;
          const isSourcesOpen = expandedSources[idx] ?? true;

          return (
            <div
              key={idx}
              className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Question as Title */}
              <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-100">
                <h3 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                  {item.question}
                </h3>
                {isVerified ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200 flex-shrink-0">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    Verified Proof
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold flex-shrink-0">
                    Unverified / Absent
                  </span>
                )}
              </div>

              {/* Answer Content */}
              <div className="mt-4 text-slate-800 text-sm sm:text-base leading-relaxed">
                {item.answer}
              </div>

              {/* Source Clause Below */}
              {item.source_clauses && item.source_clauses.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <button
                    onClick={() => toggleSource(idx)}
                    className="text-xs font-semibold text-slate-500 hover:text-slate-800 inline-flex items-center gap-1 transition-colors"
                  >
                    <FileText className="w-3.5 h-3.5 text-blue-500" />
                    <span>Source Clauses Cited ({item.source_clauses.length})</span>
                    {isSourcesOpen ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </button>

                  {isSourcesOpen && (
                    <div className="mt-2.5 space-y-2">
                      {item.source_clauses.map((clause, cIdx) => (
                        <div
                          key={cIdx}
                          className="bg-slate-50/80 rounded-xl p-3 border border-slate-200/80 text-xs text-slate-700"
                        >
                          <div className="font-semibold text-slate-900 mb-1 flex items-center justify-between">
                            <span>
                              {clause.clause_number} {clause.heading}
                            </span>
                            {clause.page_number && (
                              <span className="text-slate-400 font-normal">
                                Page {clause.page_number}
                              </span>
                            )}
                          </div>
                          <div className="font-mono text-slate-600 whitespace-pre-wrap leading-relaxed">
                            {clause.text}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {isSending && (
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm animate-pulse">
            <div className="h-5 bg-slate-200 rounded w-1/3 mb-3"></div>
            <div className="h-4 bg-slate-100 rounded w-full mb-2"></div>
            <div className="h-4 bg-slate-100 rounded w-2/3"></div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Fixed Bottom Input Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-md border-t border-slate-200/80 py-4 px-4 z-40">
        <form
          onSubmit={handleSubmit}
          className="max-w-4xl mx-auto flex items-center gap-3 relative"
        >
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder="Ask anything about this agreement (e.g. 'Can either party terminate without cause?')..."
            disabled={isSending || !contractId}
            className="flex-1 px-5 py-3.5 bg-slate-100 hover:bg-slate-50 focus:bg-white text-slate-900 placeholder:text-slate-400 text-sm md:text-base rounded-2xl border border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all"
          />
          <button
            type="submit"
            disabled={!inputQuestion.trim() || isSending || !contractId}
            className="px-5 py-3.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold rounded-2xl shadow-md shadow-blue-500/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:hover:scale-100 flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Ask</span>
          </button>
        </form>
      </div>
    </div>
  );
}
