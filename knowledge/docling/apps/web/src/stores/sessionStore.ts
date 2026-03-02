/**
 * Session Store - Zustand store for session management
 * Handles session creation, retrieval, and lifecycle
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Session } from '../types';
import { createSession, getSession } from '../lib/api';

interface SessionState {
  // State
  sessionId: string | null;
  session: Session | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  initSession: (client?: string) => Promise<string>;
  loadSession: (sessionId: string) => Promise<void>;
  clearSession: () => void;
  setError: (error: string | null) => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      // Initial state
      sessionId: null,
      session: null,
      isLoading: false,
      error: null,

      // Initialize or restore session
      initSession: async (client = 'web') => {
        const { sessionId } = get();

        // If we have a cached session, try to restore it
        if (sessionId) {
          try {
            set({ isLoading: true, error: null });
            const sessionData = await getSession(sessionId);
            set({
              session: {
                session_id: sessionData.session_id,
                created_at: sessionData.created_at,
                last_active: new Date().toISOString(),
                message_count: 0,
                client,
                metadata: sessionData.metadata,
              },
              isLoading: false,
            });
            return sessionId;
          } catch {
            // Session expired or invalid, create new one
            console.log('Cached session invalid, creating new one');
          }
        }

        // Create new session
        set({ isLoading: true, error: null });
        try {
          const response = await createSession({ client });
          const newSession: Session = {
            session_id: response.session_id,
            created_at: response.created_at,
            last_active: response.created_at,
            message_count: 0,
            client,
          };
          set({
            sessionId: response.session_id,
            session: newSession,
            isLoading: false,
          });
          return response.session_id;
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to create session';
          set({ error: errorMsg, isLoading: false });
          throw err;
        }
      },

      // Load existing session by ID
      loadSession: async (sessionId: string) => {
        set({ isLoading: true, error: null });
        try {
          const sessionData = await getSession(sessionId);
          set({
            sessionId,
            session: {
              session_id: sessionData.session_id,
              created_at: sessionData.created_at,
              last_active: new Date().toISOString(),
              message_count: 0,
              client: 'web',
              metadata: sessionData.metadata,
            },
            isLoading: false,
          });
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to load session';
          set({ error: errorMsg, isLoading: false, sessionId: null, session: null });
          throw err;
        }
      },

      // Clear session (logout/reset)
      clearSession: () => {
        set({
          sessionId: null,
          session: null,
          error: null,
        });
      },

      // Set error state
      setError: (error) => {
        set({ error });
      },
    }),
    {
      name: 'zoocari-session',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ sessionId: state.sessionId }),
    }
  )
);
