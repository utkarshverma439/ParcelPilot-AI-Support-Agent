import React, { useState, useRef, useEffect } from 'react';

export default function ChatInput({ onSend, isLoading, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [text]);

  const handleSubmit = () => {
    if (text.trim() && !isLoading && !disabled) {
      onSend(text);
      setText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 bg-gradient-to-t from-gray-50 via-gray-50 to-transparent pt-4 pb-4 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-2xl shadow-lg shadow-gray-200/50 flex items-end gap-2 p-2">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            disabled={isLoading || disabled}
            className="flex-1 px-3 py-2 text-sm text-gray-800 placeholder-gray-400 bg-transparent border-none outline-none disabled:opacity-50 min-h-[40px] max-h-[150px]"
            aria-label="Message input"
          />
          <button
            onClick={handleSubmit}
            disabled={!text.trim() || isLoading || disabled}
            className="w-10 h-10 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition-all flex-shrink-0 shadow-sm"
            aria-label="Send message"
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">
          AI responses can make mistakes. Verify important info.
        </p>
      </div>
    </div>
  );
}
