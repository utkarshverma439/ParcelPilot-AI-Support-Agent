import React, { useEffect } from 'react';
import ChatHeader from './components/ChatHeader';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import TypingIndicator from './components/TypingIndicator';
import WelcomeScreen from './components/WelcomeScreen';
import ErrorMessage from './components/ErrorMessage';
import { useChat } from './hooks/useChat';

export default function App() {
  const {
    messages,
    isLoading,
    error,
    userId,
    messagesEndRef,
    send,
    confirmPendingAction,
    clearChat,
    changeUser,
    setError,
  } = useChat();

  const isEmpty = messages.length === 0;

  const handleSuggestionClick = (text) => {
    send(text);
  };

  const handleRetry = () => {
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMsg) {
      setError(null);
      send(lastUserMsg.content);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <ChatHeader
        userId={userId}
        onClearChat={clearChat}
        onChangeUser={changeUser}
      />

      {isEmpty ? (
        <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto py-6 space-y-4">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onConfirmAction={confirmPendingAction}
              />
            ))}

            {isLoading && <TypingIndicator />}

            {error && !isLoading && (
              <ErrorMessage message={error} onRetry={handleRetry} />
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      <ChatInput
        onSend={send}
        isLoading={isLoading}
        disabled={false}
      />
    </div>
  );
}
