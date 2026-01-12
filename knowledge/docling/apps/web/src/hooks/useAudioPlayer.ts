import { useState, useRef, useEffect, useCallback } from 'react';

interface UseAudioPlayerState {
  isPlaying: boolean;
  isLoading: boolean;
  currentTime: number;
  duration: number;
  error: string | null;
}

interface UseAudioPlayerReturn extends UseAudioPlayerState {
  play: (audioBlob: Blob) => Promise<void>;
  pause: () => void;
  stop: () => void;
  seek: (time: number) => void;
  reset: () => void;
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  // Clean up Object URL
  const revokeObjectUrl = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  // Play audio from Blob
  const play = useCallback(async (audioBlob: Blob): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // Clean up previous audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      revokeObjectUrl();

      // Create new Audio element and Object URL
      const audio = new Audio();
      const objectUrl = URL.createObjectURL(audioBlob);
      objectUrlRef.current = objectUrl;
      audio.src = objectUrl;

      // Set up event listeners
      const handleLoadedMetadata = () => {
        setDuration(audio.duration);
        setIsLoading(false);
      };

      const handleTimeUpdate = () => {
        setCurrentTime(audio.currentTime);
      };

      const handleEnded = () => {
        setIsPlaying(false);
        setCurrentTime(0);
      };

      const handleError = () => {
        const audioError = audio.error;
        const errorMsg = audioError
          ? `Failed to load audio: ${audioError.code} - ${audioError.message}`
          : 'Failed to load audio: unknown error';
        console.error('[AudioPlayer] Error:', errorMsg, 'src:', audio.src);
        setError(errorMsg);
        setIsPlaying(false);
        setIsLoading(false);
      };

      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      audio.addEventListener('timeupdate', handleTimeUpdate);
      audio.addEventListener('ended', handleEnded);
      audio.addEventListener('error', handleError);

      audioRef.current = audio;

      // Load and play
      await audio.play();
      setIsPlaying(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to play audio');
      setIsPlaying(false);
      setIsLoading(false);
    }
  }, [revokeObjectUrl]);

  // Pause playback
  const pause = useCallback(() => {
    if (audioRef.current && isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, [isPlaying]);

  // Stop and reset to beginning
  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      setCurrentTime(0);
    }
  }, []);

  // Reset all state (for when audio source changes)
  const reset = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    revokeObjectUrl();
    setIsPlaying(false);
    setIsLoading(false);
    setCurrentTime(0);
    setDuration(0);
    setError(null);
  }, [revokeObjectUrl]);

  // Seek to specific time
  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(time, duration));
      setCurrentTime(audioRef.current.currentTime);
    }
  }, [duration]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      revokeObjectUrl();
    };
  }, [revokeObjectUrl]);

  return {
    isPlaying,
    isLoading,
    currentTime,
    duration,
    error,
    play,
    pause,
    stop,
    seek,
    reset,
  };
}
