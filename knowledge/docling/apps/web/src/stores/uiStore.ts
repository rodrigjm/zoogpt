/**
 * UI Store - Zustand store for ephemeral UI state
 * Handles view-only state that doesn't need persistence
 */

import { create } from 'zustand';

type InputMode = 'voice' | 'text';

interface UIState {
  // Input mode (voice vs text)
  inputMode: InputMode;
  setInputMode: (mode: InputMode) => void;
  toggleInputMode: () => void;

  // Input focus state
  isInputFocused: boolean;
  setInputFocused: (focused: boolean) => void;

  // Scroll state
  showJumpToBottom: boolean;
  setShowJumpToBottom: (show: boolean) => void;

  // Expanded sources (by message ID)
  expandedSources: Set<string>;
  toggleSourceExpanded: (messageId: string) => void;
  isSourceExpanded: (messageId: string) => boolean;

  // Feedback modal
  feedbackModalOpen: boolean;
  feedbackMessageId: string | null;
  openFeedbackModal: (messageId: string) => void;
  closeFeedbackModal: () => void;

  // Reset
  reset: () => void;
}

export const useUIStore = create<UIState>()((set, get) => ({
  // Initial state
  inputMode: 'voice',
  isInputFocused: false,
  showJumpToBottom: false,
  expandedSources: new Set<string>(),
  feedbackModalOpen: false,
  feedbackMessageId: null,

  // Input mode actions
  setInputMode: (mode) => set({ inputMode: mode }),
  toggleInputMode: () =>
    set((state) => ({
      inputMode: state.inputMode === 'voice' ? 'text' : 'voice',
    })),

  // Input focus actions
  setInputFocused: (focused) => set({ isInputFocused: focused }),

  // Scroll actions
  setShowJumpToBottom: (show) => set({ showJumpToBottom: show }),

  // Sources expansion actions
  toggleSourceExpanded: (messageId) =>
    set((state) => {
      const newSet = new Set(state.expandedSources);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return { expandedSources: newSet };
    }),
  isSourceExpanded: (messageId) => get().expandedSources.has(messageId),

  // Feedback modal actions
  openFeedbackModal: (messageId) =>
    set({ feedbackModalOpen: true, feedbackMessageId: messageId }),
  closeFeedbackModal: () =>
    set({ feedbackModalOpen: false, feedbackMessageId: null }),

  // Reset to initial state
  reset: () =>
    set({
      inputMode: 'voice',
      isInputFocused: false,
      showJumpToBottom: false,
      expandedSources: new Set<string>(),
      feedbackModalOpen: false,
      feedbackMessageId: null,
    }),
}));
