/**
 * Chat Store - Zustand store for chat/conversation management
 * Handles messages, streaming, sources, and followup questions
 */

import { create } from 'zustand';
import type { ChatMessage, Source, StreamChunk } from '../types';
import { sendChatMessage, streamChatMessage } from '../lib/api';

/**
 * Strip follow-up questions section from response text.
 * Follow-up questions are displayed as buttons, not in the message text.
 */
function stripFollowupQuestions(text: string): string {
  // Try multiple patterns to handle LLM format variations
  const patterns = [
    // **Want to explore more?...** and everything after
    /\*\*Want to explore more\?.*$/is,
    // Want to explore more? (without bold) and everything after
    /Want to explore more\?.*$/is,
    // "questions to ask" section and everything after
    /Here are some.*questions to ask.*$/is,
  ];

  let result = text;
  for (const pattern of patterns) {
    const stripped = result.replace(pattern, '').trim();
    if (stripped !== result) {
      return stripped;
    }
  }
  return result.trim();
}

interface ChatState {
  // State
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  sources: Source[];
  followupQuestions: string[];
  confidence: number | null;
  error: string | null;
  ratings: Map<string, 'up' | 'down'>;

  // Actions
  sendMessage: (sessionId: string, content: string) => Promise<void>;
  sendMessageStream: (sessionId: string, content: string) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setError: (error: string | null) => void;
  setRating: (messageId: string, rating: 'up' | 'down') => void;
  getRating: (messageId: string) => 'up' | 'down' | null;
}

export const useChatStore = create<ChatState>()((set, get) => ({
  // Initial state
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  sources: [],
  followupQuestions: [],
  confidence: null,
  error: null,
  ratings: new Map(),

  // Send message (non-streaming)
  sendMessage: async (sessionId: string, content: string) => {
    const userMessage: ChatMessage = {
      message_id: `user-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
      sources: [],
      followupQuestions: [],
      confidence: null,
    }));

    try {
      const response = await sendChatMessage({
        session_id: sessionId,
        message: content,
        mode: 'rag',
      });

      const assistantMessage: ChatMessage = {
        message_id: response.message_id,
        session_id: response.session_id,
        role: 'assistant',
        content: stripFollowupQuestions(response.reply),
        created_at: response.created_at,
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        sources: response.sources,
        followupQuestions: response.followup_questions,
        confidence: response.confidence,
        isLoading: false,
      }));
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to send message';
      set({ error: errorMsg, isLoading: false });
    }
  },

  // Send message with streaming
  sendMessageStream: async (sessionId: string, content: string) => {
    const userMessage: ChatMessage = {
      message_id: `user-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isStreaming: true,
      streamingContent: '',
      error: null,
      sources: [],
      followupQuestions: [],
      confidence: null,
    }));

    let streamedText = '';

    try {
      await streamChatMessage(
        {
          session_id: sessionId,
          message: content,
          mode: 'rag',
        },
        // onChunk
        (chunk: StreamChunk) => {
          if (chunk.type === 'text' && chunk.content) {
            streamedText += chunk.content;
            // Strip follow-up questions from displayed content during streaming
            set({ streamingContent: stripFollowupQuestions(streamedText) });
          }
        },
        // onComplete
        (data) => {
          const assistantMessage: ChatMessage = {
            message_id: `assistant-${Date.now()}`,
            session_id: sessionId,
            role: 'assistant',
            content: stripFollowupQuestions(streamedText),
            created_at: new Date().toISOString(),
          };

          set((state) => ({
            messages: [...state.messages, assistantMessage],
            sources: data.sources || [],
            followupQuestions: data.followup_questions || [],
            isStreaming: false,
            streamingContent: '',
          }));
        },
        // onError
        (error: Error) => {
          set({
            error: error.message,
            isStreaming: false,
            streamingContent: '',
          });
        }
      );
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Stream failed';
      set({
        error: errorMsg,
        isStreaming: false,
        streamingContent: '',
      });
    }
  },

  // Add a message directly (for external use)
  addMessage: (message: ChatMessage) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  // Clear all messages
  clearMessages: () => {
    set({
      messages: [],
      sources: [],
      followupQuestions: [],
      confidence: null,
      streamingContent: '',
    });
  },

  // Set error state
  setError: (error) => {
    set({ error });
  },

  // Set rating for a message
  setRating: (messageId: string, rating: 'up' | 'down') => {
    set((state) => {
      const newRatings = new Map(state.ratings);
      newRatings.set(messageId, rating);
      return { ratings: newRatings };
    });
  },

  // Get rating for a message
  getRating: (messageId: string) => {
    return get().ratings.get(messageId) ?? null;
  },
}));
