/**
 * Voice Store - Zustand store for voice/audio management
 * Uses a state machine pattern with a single `mode` field
 * Handles STT, TTS, recording, and playback state
 */

import { create } from 'zustand';
import { speechToText, textToSpeech, streamTextToSpeech } from '../lib/api';
import type { TtsStreamAudioChunk } from '../types';

// Voice mode state machine - single source of truth
export type VoiceMode = 'idle' | 'recording' | 'processing' | 'playing';

interface VoiceState {
  // State machine - single source of truth
  mode: VoiceMode;

  // Data
  transcribedText: string;
  audioUrl: string | null;
  error: string | null;
  selectedVoice: string;
  useWebSocket: boolean;

  // Recording internals (not persisted)
  mediaRecorder: MediaRecorder | null;
  audioChunks: Blob[];

  // Streaming state
  streamingSentences: string[];
  currentSentenceIndex: number;

  // Actions
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  transcribe: (sessionId: string, audioBlob: Blob) => Promise<string>;
  speak: (sessionId: string, text: string) => Promise<void>;
  speakStreaming: (sessionId: string, message: string, onSentence?: (sentence: string) => void) => Promise<void>;
  stopPlayback: () => void;
  setVoice: (voice: string) => void;
  setError: (error: string | null) => void;
  toggleWebSocket: () => void;
  reset: () => void;
}

// Selectors for derived state (use these in components)
export const selectIsRecording = (state: VoiceState) => state.mode === 'recording';
export const selectIsProcessing = (state: VoiceState) => state.mode === 'processing';
export const selectIsPlaying = (state: VoiceState) => state.mode === 'playing';
export const selectIsIdle = (state: VoiceState) => state.mode === 'idle';
export const selectIsBusy = (state: VoiceState) => state.mode !== 'idle';

export const useVoiceStore = create<VoiceState>()((set, get) => ({
  // Initial state
  mode: 'idle',
  transcribedText: '',
  audioUrl: null,
  error: null,
  selectedVoice: 'bella',
  useWebSocket: true,
  mediaRecorder: null,
  audioChunks: [],
  streamingSentences: [],
  currentSentenceIndex: 0,

  // Start recording from microphone
  startRecording: async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Prefer webm for better browser support
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

      const recorder = new MediaRecorder(stream, { mimeType });
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.start();

      set({
        mediaRecorder: recorder,
        audioChunks: chunks,
        mode: 'recording',
        error: null,
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Microphone access denied';
      set({ error: errorMsg });
      throw err;
    }
  },

  // Stop recording and return audio blob
  stopRecording: async () => {
    const { mediaRecorder, audioChunks } = get();

    if (!mediaRecorder) {
      return null;
    }

    return new Promise<Blob>((resolve) => {
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });

        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach((track) => track.stop());

        set({
          mediaRecorder: null,
          audioChunks: [],
          mode: 'idle',
        });

        resolve(blob);
      };

      mediaRecorder.stop();
    });
  },

  // Transcribe audio to text (STT)
  transcribe: async (sessionId: string, audioBlob: Blob) => {
    set({ mode: 'processing', error: null });

    try {
      // Convert blob to File for FormData
      const file = new File([audioBlob], 'recording.webm', { type: audioBlob.type });

      const response = await speechToText({
        session_id: sessionId,
        audio: file,
      });

      set({
        transcribedText: response.text,
        mode: 'idle',
      });

      return response.text;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Transcription failed';
      set({ error: errorMsg, mode: 'idle' });
      throw err;
    }
  },

  // Convert text to speech and play (TTS)
  speak: async (sessionId: string, text: string) => {
    const { selectedVoice, audioUrl: previousUrl } = get();

    // Clean up previous audio
    if (previousUrl) {
      URL.revokeObjectURL(previousUrl);
    }

    set({ mode: 'processing', error: null });

    try {
      const audioBlob = await textToSpeech({
        session_id: sessionId,
        text,
        voice: selectedVoice,
      });

      const url = URL.createObjectURL(audioBlob);
      const audio = new Audio(url);

      set({
        audioUrl: url,
        mode: 'playing',
      });

      audio.onended = () => {
        set({ mode: 'idle' });
      };

      audio.onerror = () => {
        set({
          error: 'Audio playback failed',
          mode: 'idle',
        });
      };

      await audio.play();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Text-to-speech failed';
      set({ error: errorMsg, mode: 'idle' });
      throw err;
    }
  },

  // Convert text to speech with streaming (low-latency)
  // Generates response from RAG and streams audio sentence-by-sentence
  speakStreaming: async (sessionId: string, message: string, onSentence?: (sentence: string) => void) => {
    const { selectedVoice, audioUrl: previousUrl } = get();

    // Clean up previous audio
    if (previousUrl) {
      URL.revokeObjectURL(previousUrl);
    }

    set({
      mode: 'processing',
      error: null,
      streamingSentences: [],
      currentSentenceIndex: 0,
    });

    // Audio queue for sequential playback
    const audioQueue: Blob[] = [];
    let isPlayingQueue = false;
    let stopRequested = false;
    let processingComplete = false;

    // Helper to convert base64 to Blob
    const base64ToBlob = (base64: string, mimeType: string = 'audio/wav'): Blob => {
      const binaryString = atob(base64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      return new Blob([bytes], { type: mimeType });
    };

    // Play audio chunks sequentially
    const playNextInQueue = async () => {
      if (stopRequested || audioQueue.length === 0) {
        isPlayingQueue = false;
        // Check if we're done
        if (audioQueue.length === 0 && processingComplete) {
          set({ mode: 'idle' });
        }
        return;
      }

      isPlayingQueue = true;
      const audioBlob = audioQueue.shift()!;
      const url = URL.createObjectURL(audioBlob);
      const audio = new Audio(url);

      set({ audioUrl: url, mode: 'playing' });

      audio.onended = () => {
        URL.revokeObjectURL(url);
        set({ currentSentenceIndex: get().currentSentenceIndex + 1 });
        playNextInQueue();
      };

      audio.onerror = () => {
        URL.revokeObjectURL(url);
        console.warn('Audio chunk playback failed, skipping to next');
        playNextInQueue();
      };

      try {
        await audio.play();
      } catch (err) {
        console.warn('Failed to play audio chunk:', err);
        playNextInQueue();
      }
    };

    try {
      await streamTextToSpeech(
        {
          session_id: sessionId,
          message,
          voice: selectedVoice,
        },
        // onAudioChunk - called for each sentence's audio
        (chunk: TtsStreamAudioChunk) => {
          // Add sentence to display
          set((state) => ({
            streamingSentences: [...state.streamingSentences, chunk.sentence],
          }));

          // Notify caller
          if (onSentence) {
            onSentence(chunk.sentence);
          }

          // Convert base64 to blob and add to queue
          const audioBlob = base64ToBlob(chunk.chunk);
          audioQueue.push(audioBlob);

          // Start playing if not already
          if (!isPlayingQueue) {
            playNextInQueue();
          }
        },
        // onComplete
        () => {
          processingComplete = true;
          // Queue will continue playing remaining chunks
          if (!isPlayingQueue && audioQueue.length === 0) {
            set({ mode: 'idle' });
          }
        },
        // onError
        (error) => {
          set({
            error: error.message,
            mode: 'idle',
          });
        }
      );
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Streaming TTS failed';
      set({ error: errorMsg, mode: 'idle' });
      throw err;
    }
  },

  // Stop audio playback
  stopPlayback: () => {
    // Note: We'd need to store the Audio element to stop it
    // For now, this just resets the state
    set({ mode: 'idle' });
  },

  // Set voice preference
  setVoice: (voice: string) => {
    set({ selectedVoice: voice });
  },

  // Set error
  setError: (error) => {
    set({ error });
  },

  // Toggle WebSocket usage
  toggleWebSocket: () => {
    set((state) => ({ useWebSocket: !state.useWebSocket }));
  },

  // Reset store to initial state
  reset: () => {
    const { audioUrl, mediaRecorder } = get();

    // Clean up
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    if (mediaRecorder) {
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
    }

    set({
      mode: 'idle',
      transcribedText: '',
      audioUrl: null,
      error: null,
      mediaRecorder: null,
      audioChunks: [],
      streamingSentences: [],
      currentSentenceIndex: 0,
    });
  },
}));

// Backwards-compatible hooks for existing components
// These derive boolean state from the mode state machine
export const useIsRecording = () => useVoiceStore(selectIsRecording);
export const useIsProcessing = () => useVoiceStore(selectIsProcessing);
export const useIsPlaying = () => useVoiceStore(selectIsPlaying);
export const useIsVoiceBusy = () => useVoiceStore(selectIsBusy);
