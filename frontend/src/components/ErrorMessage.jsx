import React from 'react';

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="flex justify-center px-4 py-3 animate-fade-in">
      <div className="bg-red-50 border border-red-200 rounded-2xl px-5 py-4 max-w-md text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <p className="text-sm font-semibold text-red-800">Something went wrong</p>
        </div>
        <p className="text-xs text-red-600 mb-3">
          {message || "I couldn't process your request right now. Please try again."}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-1.5 text-xs font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded-lg transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
