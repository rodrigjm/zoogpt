/**
 * Voice Store - Zustand store for voice/audio management
 * Handles STT, TTS, recording, and playback state
 */

import { create } from 'zustand';
import { speechToText, textToSpeech } from '../lib/api';

type VoiceMode = 'idle' | 'recording' | 'processing' | 'playing';

interface VoiceState {
  // State
  mode: VoiceMode;
  isRecording: boolean;
  isProcessing: boolean;
  isPlaying: boolean;
  transcribedText: string;
  audioUrl: string | null;
  error: string | null;
  selectedVoice: string;

  // Recording internals (not persisted)
  mediaRecorder: MediaRecorder | null;
  audioChunks: Blob[];

  // Actions
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  transcribe: (sessionId: string, audioBlob: Blob) => Promise<string>;
  speak: (sessionId: string, text: string) => Promise<void>;
  stopPlayback: () => void;
  setVoice: (voice: string) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useVoiceStore = create<VoiceState>()((set, get) => ({
  // Initial state
  mode: 'idle',
  isRecording: false,
  isProcessing: false,
  isPlaying: false,
  transcribedText: '',
  audioUrl: null,
  error: null,
  selectedVoice: 'bella',
  mediaRecorder: null,
  audioChunks: [],

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
        isRecording: true,
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
          isRecording: false,
          mode: 'idle',
        });

        resolve(blob);
      };

      mediaRecorder.stop();
    });
  },

  // Transcribe audio to text (STT)
  transcribe: async (sessionId: string, audioBlob: Blob) => {
    set({ isProcessing: true, mode: 'processing', error: null });

    try {
      // Convert blob to File for FormData
      const file = new File([audioBlob], 'recording.webm', { type: audioBlob.type });

      const response = await speechToText({
        session_id: sessionId,
        audio: file,
      });

      set({
        transcribedText: response.text,
        isProcessing: false,
        mode: 'idle',
      });

      return response.text;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Transcription failed';
      set({ error: errorMsg, isProcessing: false, mode: 'idle' });
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

    set({ isProcessing: true, mode: 'processing', error: null });

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
        isProcessing: false,
        isPlaying: true,
        mode: 'playing',
      });

      audio.onended = () => {
        set({ isPlaying: false, mode: 'idle' });
      };

      audio.onerror = () => {
        set({
          error: 'Audio playback failed',
          isPlaying: false,
          mode: 'idle',
        });
      };

      await audio.play();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Text-to-speech failed';
      set({ error: errorMsg, isProcessing: false, mode: 'idle' });
      throw err;
    }
  },

  // Stop audio playback
  stopPlayback: () => {
    // Note: We'd need to store the Audio element to stop it
    // For now, this just resets the state
    set({ isPlaying: false, mode: 'idle' });
  },

  // Set voice preference
  setVoice: (voice: string) => {
    set({ selectedVoice: voice });
  },

  // Set error
  setError: (error) => {
    set({ error });
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
      isRecording: false,
      isProcessing: false,
      isPlaying: false,
      transcribedText: '',
      audioUrl: null,
      error: null,
      mediaRecorder: null,
      audioChunks: [],
    });
  },
}));
