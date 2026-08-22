import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import ParcelCard from './ParcelCard';
import { confirmAction } from '../services/api';

export default function ChatMessage({ message, onConfirmAction }) {
  const [confirmingId, setConfirmingId] = useState(null);
  const [confirmResult, setConfirmResult] = useState({});

  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isAssistant = message.role === 'assistant';

  const handleConfirm = async (actionId) => {
    setConfirmingId(actionId);
    try {
      const result = await onConfirmAction(actionId);
      setConfirmResult(prev => ({ ...prev, [actionId]: result }));
    } catch (err) {
      setConfirmResult(prev => ({ ...prev, [actionId]: { error: err.message } }));
    } finally {
      setConfirmingId(null);
    }
  };

  if (isSystem) {
    return (
      <div className="flex justify-center px-4 py-2 animate-fade-in">
        <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-full text-sm text-yellow-700">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 px-4 animate-fade-in ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {isAssistant && (
        <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
          </svg>
        </div>
      )}

      <div className={`max-w-[85%] sm:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-br-md'
              : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md'
          }`}
        >
          {isAssistant ? (
            <div className="text-sm leading-relaxed prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-sm leading-relaxed">{message.content}</p>
          )}
        </div>

        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="mt-2 ml-1">
            <details className="group">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 select-none">
                📚 Sources ({message.citations.length})
              </summary>
              <div className="mt-2 space-y-1.5">
                {message.citations.map((c, i) => (
                  <div key={i} className="text-xs bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
                    <span className="font-medium text-gray-700">{c.document || 'Unknown'}</span>
                    {c.page && <span className="text-gray-400"> — Page {c.page}</span>}
                    {c.excerpt && <p className="text-gray-500 mt-1 line-clamp-2">{c.excerpt}</p>}
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {isAssistant && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 ml-1">
            <details className="group">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 select-none">
                🔧 Tools used ({message.toolCalls.length})
              </summary>
              <div className="mt-2 space-y-1.5">
                {message.toolCalls.map((tc, i) => (
                  <div key={i} className="text-xs bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 font-mono">
                    <span className="font-medium text-primary-600">{tc.tool}</span>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {isAssistant && message.pendingActions && message.pendingActions.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.pendingActions.map((action, i) => (
              <div key={action.action_id || i} className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                <p className="text-xs font-medium text-amber-800 mb-2">
                  ⚠️ {action.action_type || 'Action'} requires confirmation
                </p>
                <p className="text-xs text-amber-700 mb-3 whitespace-pre-line">{action.message}</p>
                {confirmResult[action.action_id] ? (
                  <p className="text-xs text-green-700 font-medium">
                    ✅ {confirmResult[action.action_id].message || 'Action executed'}
                  </p>
                ) : (
                  <button
                    onClick={() => handleConfirm(action.action_id)}
                    disabled={confirmingId === action.action_id}
                    className="px-4 py-1.5 text-xs font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
                  >
                    {confirmingId === action.action_id ? 'Confirming...' : 'Confirm Action'}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {isAssistant && message.conflicts && message.conflicts.length > 0 && (
          <div className="mt-2 ml-1">
            <details className="group">
              <summary className="text-xs text-red-500 cursor-pointer hover:text-red-700 select-none">
                ⚠️ Source conflicts ({message.conflicts.length})
              </summary>
              <div className="mt-2 space-y-1.5">
                {message.conflicts.map((c, i) => (
                  <div key={i} className="text-xs bg-red-50 border border-red-100 rounded-lg px-3 py-2 text-red-700">
                    {c.document_type}: {c.resolution || 'Check source priority'}
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {isAssistant && message.confidence && (
          <div className="mt-1.5 ml-1">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              message.confidence === 'high' ? 'bg-green-50 text-green-600' :
              message.confidence === 'medium' ? 'bg-yellow-50 text-yellow-600' :
              'bg-red-50 text-red-600'
            }`}>
              {message.confidence} confidence
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
