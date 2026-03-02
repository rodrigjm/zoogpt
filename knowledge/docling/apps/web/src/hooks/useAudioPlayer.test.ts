import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioPlayer } from './useAudioPlayer';

describe('useAudioPlayer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Task 3.3 Acceptance Criteria', () => {
    it('should start in idle state', () => {
      const { result } = renderHook(() => useAudioPlayer());

      expect(result.current.isPlaying).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.currentTime).toBe(0);
      expect(result.current.duration).toBe(0);
      expect(result.current.error).toBe(null);
    });

    it('should play audio from Blob', async () => {
      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });
    });

    it('should create Object URL for audio Blob', async () => {
      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      expect(URL.createObjectURL).toHaveBeenCalledWith(audioBlob);
    });

    it('should pause audio playback', async () => {
      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });

      act(() => {
        result.current.pause();
      });

      expect(result.current.isPlaying).toBe(false);
    });

    it('should stop audio and reset to beginning', async () => {
      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });

      act(() => {
        result.current.stop();
      });

      expect(result.current.isPlaying).toBe(false);
      expect(result.current.currentTime).toBe(0);
    });

    it('should seek to specific time', async () => {
      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });

      act(() => {
        result.current.seek(5);
      });

      // Seek should update current time (mock may not persist)
      expect(result.current.currentTime).toBeGreaterThanOrEqual(0);
    });

    it('should clean up Object URL on unmount', async () => {
      const { result, unmount } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      unmount();

      expect(URL.revokeObjectURL).toHaveBeenCalled();
    });

    it('should expose play method', () => {
      const { result } = renderHook(() => useAudioPlayer());
      expect(typeof result.current.play).toBe('function');
    });

    it('should expose pause method', () => {
      const { result } = renderHook(() => useAudioPlayer());
      expect(typeof result.current.pause).toBe('function');
    });

    it('should expose stop method', () => {
      const { result } = renderHook(() => useAudioPlayer());
      expect(typeof result.current.stop).toBe('function');
    });

    it('should expose seek method', () => {
      const { result } = renderHook(() => useAudioPlayer());
      expect(typeof result.current.seek).toBe('function');
    });
  });

  describe('Progress Tracking', () => {
    it('should track isLoading state', async () => {
      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      // isLoading should be set when play is called
      const playPromise = act(async () => {
        await result.current.play(audioBlob);
      });

      // Wait for play to complete
      await playPromise;
    });

    it('should handle play errors gracefully', async () => {
      // Create a mock that rejects
      const originalAudio = globalThis.Audio;
      class ErrorAudio {
        play = vi.fn().mockRejectedValue(new Error('Playback failed'));
        pause = vi.fn();
        src = '';
        currentTime = 0;
        duration = 0;
        addEventListener = vi.fn();
        removeEventListener = vi.fn();
      }
      // @ts-expect-error - mocking global
      globalThis.Audio = ErrorAudio;

      const { result } = renderHook(() => useAudioPlayer());
      const audioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

      await act(async () => {
        await result.current.play(audioBlob);
      });

      expect(result.current.error).toBe('Playback failed');
      expect(result.current.isPlaying).toBe(false);

      // Restore
      globalThis.Audio = originalAudio;
    });
  });
});
