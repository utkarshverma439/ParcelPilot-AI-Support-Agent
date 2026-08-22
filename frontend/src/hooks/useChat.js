import { useState, useCallback, useRef, useEffect } from 'react';
import { sendMessage, confirmAction } from '../services/api';

const STORAGE_KEY = 'parcelpilot_session_id';
const USER_KEY = 'parcelpilot_user_id';

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function getStoredSessionId() {
  try {
    return localStorage.getItem(STORAGE_KEY) || generateSessionId();
  } catch {
    return generateSessionId();
  }
}

function getStoredUserId() {
  try {
    return localStorage.getItem(USER_KEY) || 'customer_northstar';
  } catch {
    return 'customer_northstar';
  }
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(getStoredSessionId);
  const [userId, setUserId] = useState(getStoredUserId);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, sessionId);
    } catch {}
  }, [sessionId]);

  useEffect(() => {
    try {
      localStorage.setItem(USER_KEY, userId);
    } catch {}
  }, [userId]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  const addMessage = useCallback((role, content, extra = {}) => {
    const msg = {
      id: Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      role,
      content,
      timestamp: new Date().toISOString(),
      ...extra,
    };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, []);

  const send = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    setError(null);
    addMessage('user', text.trim());
    setIsLoading(true);

    try {
      const data = await sendMessage(text.trim(), userId);

      const isAccessDenied = data.response && data.response.includes('Access denied');
      const isSecurityBlock = data.response && (
        data.response.includes('unsupported instructions') ||
        data.response.includes('Request blocked')
      );

      addMessage('assistant', data.response, {
        citations: data.citations || [],
        toolCalls: data.tool_calls || [],
        conflicts: data.conflicts || [],
        confidence: data.confidence || 'medium',
        pendingActions: data.pending_actions || [],
        messageType: isSecurityBlock ? 'security' : 'text',
      });
    } catch (err) {
      setError(err.message);
      addMessage('system', 'Something went wrong. Please try again.', {
        messageType: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  }, [userId, isLoading, addMessage]);

  const confirmPendingAction = useCallback(async (actionId) => {
    try {
      const result = await confirmAction(actionId);
      setMessages(prev =>
        prev.map(msg => {
          if (msg.pendingActions) {
            return {
              ...msg,
              pendingActions: msg.pendingActions.map(a =>
                a.action_id === actionId
                  ? { ...a, status: 'executed', message: result.message }
                  : a
              ),
            };
          }
          return msg;
        })
      );
      return result;
    } catch (err) {
      throw err;
    }
  }, []);

  const clearChat = useCallback(() => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    setMessages([]);
    setError(null);
    setIsLoading(false);
  }, []);

  const changeUser = useCallback((newUserId) => {
    setUserId(newUserId);
    clearChat();
  }, [clearChat]);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    userId,
    messagesEndRef,
    send,
    confirmPendingAction,
    clearChat,
    changeUser,
    setError,
  };
}
