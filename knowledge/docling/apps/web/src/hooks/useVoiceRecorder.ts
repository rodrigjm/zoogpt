import { useState, useRef, useEffect, useCallback } from 'react';

interface UseVoiceRecorderState {
  isRecording: boolean;
  isPreparing: boolean;
  audioBlob: Blob | null;
  duration: number;
  error: string | null;
}

interface UseVoiceRecorderReturn extends UseVoiceRecorderState {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  cancelRecording: () => void;
  reset: () => void;
}

export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const [state, setState] = useState<UseVoiceRecorderState>({
    isRecording: false,
    isPreparing: false,
    audioBlob: null,
    duration: 0,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);

  // Cleanup function for stream tracks
  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, []);

  // Cleanup timer
  const cleanupTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Determine best MIME type for current browser
  const getMimeType = useCallback((): string => {
    const types = ['audio/webm', 'audio/mp4'];
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    // Fallback to empty string (browser default)
    return '';
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isPreparing: true, error: null }));

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Determine MIME type
      const mimeType = getMimeType();
      const options = mimeType ? { mimeType } : undefined;

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Start recording
      mediaRecorder.start();
      startTimeRef.current = Date.now();

      // Start duration timer (update every 100ms)
      timerRef.current = setInterval(() => {
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        setState(prev => ({ ...prev, duration: elapsed }));
      }, 100);

      setState(prev => ({
        ...prev,
        isRecording: true,
        isPreparing: false,
        duration: 0,
      }));
    } catch (err) {
      let errorMessage = 'Failed to start recording';
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError' || err.message.includes('Permission denied')) {
          errorMessage = 'Microphone access denied. Please allow microphone in browser settings and refresh.';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No microphone found. Please connect a microphone.';
        } else {
          errorMessage = err.message;
        }
      }
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isPreparing: false,
        isRecording: false,
      }));
      cleanupStream();
    }
  }, [getMimeType, cleanupStream]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve(null);
        return;
      }

      // Handle stop event
      mediaRecorder.onstop = () => {
        const mimeType = getMimeType();
        const blob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' });

        setState(prev => ({
          ...prev,
          isRecording: false,
          audioBlob: blob,
        }));

        cleanupTimer();
        cleanupStream();

        resolve(blob);
      };

      mediaRecorder.stop();
    });
  }, [getMimeType, cleanupTimer, cleanupStream]);

  const cancelRecording = useCallback(() => {
    const mediaRecorder = mediaRecorderRef.current;

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }

    chunksRef.current = [];

    setState(prev => ({
      ...prev,
      isRecording: false,
      audioBlob: null,
      duration: 0,
    }));

    cleanupTimer();
    cleanupStream();
  }, [cleanupTimer, cleanupStream]);

  const reset = useCallback(() => {
    cancelRecording();
    setState({
      isRecording: false,
      isPreparing: false,
      audioBlob: null,
      duration: 0,
      error: null,
    });
  }, [cancelRecording]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupTimer();
      cleanupStream();
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, [cleanupTimer, cleanupStream]);

  return {
    ...state,
    startRecording,
    stopRecording,
    cancelRecording,
    reset,
  };
}
