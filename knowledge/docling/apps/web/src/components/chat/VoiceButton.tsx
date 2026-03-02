import React, { useEffect, useRef } from 'react';
import { useVoiceStore } from '../../stores/voiceStore';
import { useSessionStore } from '../../stores/sessionStore';

interface VoiceButtonProps {
  onTranscript?: (text: string) => void;
  disabled?: boolean;
}

export default function VoiceButton({ onTranscript, disabled = false }: VoiceButtonProps) {
  const { mode, startRecording, stopRecording, transcribe, error } = useVoiceStore();
  const sessionId = useSessionStore((state) => state.sessionId);
  const isProcessing = useRef(false);

  // Handle voice mode changes
  useEffect(() => {
    if (error) {
      console.error('Voice error:', error);
    }
  }, [error]);

  const handleClick = async () => {
    if (disabled || !sessionId) return;

    if (mode === 'idle') {
      // Start recording
      try {
        await startRecording();
      } catch (err) {
        console.error('Failed to start recording:', err);
      }
    } else if (mode === 'recording') {
      // Stop recording and transcribe
      if (isProcessing.current) return;
      isProcessing.current = true;

      try {
        const audioBlob = await stopRecording();
        if (audioBlob) {
          const text = await transcribe(sessionId, audioBlob);
          if (text && onTranscript) {
            onTranscript(text);
          }
        }
      } catch (err) {
        console.error('Failed to transcribe:', err);
      } finally {
        isProcessing.current = false;
      }
    }
  };

  // Get button color based on mode
  const getButtonColor = () => {
    switch (mode) {
      case 'idle':
        return 'bg-voice-idle';
      case 'recording':
        return 'bg-voice-recording';
      case 'processing':
        return 'bg-voice-processing';
      case 'playing':
        return 'bg-voice-playing';
      default:
        return 'bg-voice-idle';
    }
  };

  const isIdle = mode === 'idle';
  const isRecording = mode === 'recording';
  const isProcessingOrPlaying = mode === 'processing' || mode === 'playing';

  return (
    <button
      onClick={handleClick}
      disabled={disabled || isProcessingOrPlaying}
      className={`
        w-12 h-12 rounded-full flex items-center justify-center
        ${getButtonColor()}
        ${isRecording ? 'animate-pulse-ring' : ''}
        shadow-md transition-all duration-200
        active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed
      `}
      aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      type="button"
    >
      {isProcessingOrPlaying ? (
        <svg
          className="w-6 h-6 text-white animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        <svg
          className="w-6 h-6 text-white"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            fillRule="evenodd"
            d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </button>
  );
}
