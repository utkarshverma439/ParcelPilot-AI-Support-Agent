import React from 'react';

const SUGGESTIONS = [
  { icon: '📦', text: 'Track my parcel' },
  { icon: '🚚', text: 'Where is my order?' },
  { icon: '📅', text: 'When will my parcel arrive?' },
  { icon: '💬', text: 'I need help with my delivery' },
];

export default function WelcomeScreen({ onSuggestionClick }) {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="text-center max-w-md animate-fade-in">
        <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary-200">
          <span className="text-4xl">📦</span>
        </div>

        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          ParcelPilot AI Support
        </h2>
        <p className="text-gray-500 mb-8 leading-relaxed">
          Your intelligent delivery assistant.
          <br />
          Ask me about your parcel, delivery,
          <br />
          tracking status, or account support.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestionClick(s.text)}
              className="flex items-center gap-3 px-4 py-3 bg-white border border-gray-200 rounded-xl text-left hover:border-primary-300 hover:shadow-md transition-all group"
            >
              <span className="text-xl">{s.icon}</span>
              <span className="text-sm font-medium text-gray-700 group-hover:text-primary-600 transition-colors">
                {s.text}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
