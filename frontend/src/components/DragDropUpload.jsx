import React, { useState, useRef } from 'react';
import { Upload, FileText, ShieldAlert, Sparkles, AlertCircle } from 'lucide-react';

export default function DragDropUpload({ onUpload, isUploading }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    setErrorMessage('');
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndUpload(files[0]);
    }
  };

  const handleFileChange = (e) => {
    setErrorMessage('');
    if (e.target.files && e.target.files.length > 0) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const validateAndUpload = (file) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMessage('Please select a valid PDF contract file.');
      return;
    }
    onUpload(file);
  };

  return (
    <div className="w-full max-w-3xl mx-auto my-8">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current && fileInputRef.current.click()}
        className={`relative border-2 border-dashed rounded-3xl p-10 md:p-14 text-center cursor-pointer transition-all duration-300 ${
          isDragOver
            ? 'border-[#EF8557] bg-[#EF8557]/10 scale-[1.01] shadow-xl'
            : 'border-slate-300 hover:border-[#EF8557]/80 bg-white/90 hover:bg-[#EF8557]/5 shadow-sm hover:shadow-md'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="application/pdf"
          className="hidden"
          disabled={isUploading}
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-[#EF8557] to-[#f49e79] text-white flex items-center justify-center shadow-lg shadow-[#EF8557]/30 group-hover:scale-105 transition-transform duration-300">
            {isUploading ? (
              <div className="w-8 h-8 border-3 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Upload className="w-9 h-9" />
            )}
          </div>

          <div className="space-y-1">
            <h3 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">
              {isUploading ? 'Uploading & Splitting Clauses...' : 'Upload Contract PDF'}
            </h3>
            <p className="text-sm md:text-base text-slate-500 max-w-md mx-auto">
              Drag and drop your agreement here, or click to browse. Fully offline & private.
            </p>
          </div>

          <button
            type="button"
            disabled={isUploading}
            className="mt-2 inline-flex items-center gap-2 px-6 py-3 bg-[#EF8557] hover:bg-[#e47242] active:bg-[#d6602e] text-white font-semibold rounded-xl shadow-md shadow-[#EF8557]/25 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            Select PDF File
          </button>

          <div className="pt-3 flex items-center gap-4 text-xs font-medium text-slate-400">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Local Ollama (qwen2.5:3b)
            </span>
            <span>•</span>
            <span>ChromaDB Vector Store</span>
            <span>•</span>
            <span>Zero Cloud Calls</span>
          </div>
        </div>

        {errorMessage && (
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-red-50 text-red-700 text-sm font-medium rounded-lg border border-red-200">
            <AlertCircle className="w-4 h-4" />
            {errorMessage}
          </div>
        )}
      </div>
    </div>
  );
}
