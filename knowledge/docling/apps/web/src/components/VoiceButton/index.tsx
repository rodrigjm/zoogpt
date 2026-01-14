import React, { useState, useCallback, useEffect } from 'react';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { speechToText } from '../../lib/api';

interface VoiceButtonProps {
  sessionId: string;
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

type ButtonState = 'idle' | 'preparing' | 'recording' | 'processing';

export default function VoiceButton({
  sessionId,
  onTranscript,
  disabled = false,
}: VoiceButtonProps) {
  const {
    isRecording,
    isPreparing,
    duration,
    error: recorderError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceRecorder();

  const [buttonState, setButtonState] = useState<ButtonState>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync button state with recorder state
  useEffect(() => {
    if (isPreparing) {
      setButtonState('preparing');
    } else if (isRecording) {
      setButtonState('recording');
    } else if (buttonState === 'processing') {
      // Keep processing state until STT completes
      return;
    } else {
      setButtonState('idle');
    }
  }, [isPreparing, isRecording]);

  // Display recorder errors
  useEffect(() => {
    if (recorderError) {
      setErrorMessage(recorderError);
      setTimeout(() => {
        setErrorMessage(null);
      }, 3000);
    }
  }, [recorderError]);

  const handleClick = useCallback(async () => {
    if (disabled) return;

    if (buttonState === 'idle') {
      // Start recording
      await startRecording();
    } else if (buttonState === 'recording') {
      // Stop recording and process
      setButtonState('processing');
      try {
        const audioBlob = await stopRecording();
        if (audioBlob) {
          // Convert Blob to File for type safety with FormData
          const audioFile = new File([audioBlob], 'recording.webm', { type: audioBlob.type });
          const response = await speechToText({
            session_id: sessionId,
            audio: audioFile,
          });
          onTranscript(response.text);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to process audio';
        setErrorMessage(message);
        setTimeout(() => {
          setErrorMessage(null);
        }, 3000);
      } finally {
        setButtonState('idle');
      }
    }
  }, [buttonState, disabled, startRecording, stopRecording, sessionId, onTranscript]);

  const handleCancel = useCallback(() => {
    cancelRecording();
    setButtonState('idle');
  }, [cancelRecording]);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getAriaLabel = (): string => {
    switch (buttonState) {
      case 'idle':
        return 'Start recording';
      case 'recording':
        return 'Stop recording';
      case 'preparing':
        return 'Preparing microphone';
      case 'processing':
        return 'Processing audio';
    }
  };

  // Visual states
  const getButtonClasses = (): string => {
    const baseClasses = 'relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer focus:outline-none focus:ring-4';

    if (disabled) {
      return `${baseClasses} bg-gray-300 cursor-not-allowed`;
    }

    switch (buttonState) {
      case 'idle':
        return `${baseClasses} bg-gradient-to-br from-leesburg-yellow to-yellow-500 hover:shadow-lg animate-pulse focus:ring-yellow-300`;
      case 'preparing':
        return `${baseClasses} bg-gray-400 focus:ring-gray-300`;
      case 'recording':
        return `${baseClasses} bg-gradient-to-br from-leesburg-orange to-red-500 shadow-lg animate-pulse focus:ring-red-300`;
      case 'processing':
        return `${baseClasses} bg-gray-400 focus:ring-gray-300`;
      default:
        return baseClasses;
    }
  };

  const renderIcon = () => {
    switch (buttonState) {
      case 'idle':
        return (
          <svg
            className="w-10 h-10 text-white"
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
        );
      case 'preparing':
        return (
          <div className="flex flex-col items-center">
            <svg
              className="w-8 h-8 text-white animate-spin"
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
            <span className="text-xs text-white mt-1">Preparing...</span>
          </div>
        );
      case 'recording':
        return (
          <div className="relative">
            <div className="w-6 h-6 bg-white rounded-full animate-pulse" />
          </div>
        );
      case 'processing':
        return (
          <div className="flex flex-col items-center">
            <svg
              className="w-8 h-8 text-white animate-spin"
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
            <span className="text-xs text-white mt-1">Processing...</span>
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || buttonState === 'preparing' || buttonState === 'processing'}
        className={getButtonClasses()}
        aria-label={getAriaLabel()}
        aria-busy={buttonState === 'processing' || buttonState === 'preparing'}
      >
        {renderIcon()}
      </button>

      {buttonState === 'recording' && (
        <div className="flex items-center gap-3">
          <span className="text-sm font-mono text-gray-700">
            {formatDuration(duration)}
          </span>
          <button
            type="button"
            onClick={handleCancel}
            className="min-w-11 min-h-11 w-11 h-11 rounded-full bg-gray-300 hover:bg-gray-400 flex items-center justify-center transition-colors"
            aria-label="Cancel recording"
          >
            <svg
              className="w-5 h-5 text-gray-700"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="absolute mt-24 px-4 py-2 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm max-w-xs text-center">
          {errorMessage}
        </div>
      )}
    </div>
  );
}
