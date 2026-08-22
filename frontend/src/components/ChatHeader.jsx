import React from 'react';

const USER_OPTIONS = {
  customer_northstar: 'Customer: Northstar Logistics',
  customer_lumenworks: 'Customer: LumenWorks',
  support_agent: 'Internal: Support Agent',
  operations_admin: 'Internal: Operations Admin',
};

export default function ChatHeader({ userId, onClearChat, onChangeUser }) {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-white text-lg">📦</span>
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-900 leading-tight">ParcelPilot</h1>
            <p className="text-xs text-gray-500">AI Support Agent</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={userId}
            onChange={(e) => onChangeUser(e.target.value)}
            className="text-xs bg-gray-50 border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent cursor-pointer"
            aria-label="Select user"
          >
            {Object.entries(USER_OPTIONS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-green-50 rounded-full border border-green-200">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-xs font-medium text-green-700">AI Online</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-gray-50 rounded-full border border-gray-200">
            <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
            </svg>
            <span className="text-xs font-medium text-gray-600">Secure</span>
          </div>

          <button
            onClick={onClearChat}
            className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Start new chat"
          >
            New Chat
          </button>
        </div>
      </div>
    </header>
  );
}
