import React from 'react';
import { useVoiceStore } from '../../stores/voiceStore';

interface VoiceOverlayProps {
  onCancel: () => void;
}

export default function VoiceOverlay({ onCancel }: VoiceOverlayProps) {
  const mode = useVoiceStore((state) => state.mode);

  const isRecording = mode === 'recording';
  const isProcessing = mode === 'processing';

  const getStatusText = () => {
    if (isRecording) return 'Listening...';
    if (isProcessing) return 'Processing...';
    return 'Ready';
  };

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        className="flex flex-col items-center gap-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Large mic button */}
        <div
          className={`
            relative w-32 h-32 rounded-full flex items-center justify-center
            ${isRecording ? 'bg-voice-recording animate-pulse-ring' : 'bg-voice-processing'}
            shadow-2xl
          `}
        >
          {isProcessing ? (
            <svg
              className="w-16 h-16 text-white animate-spin"
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
              className="w-16 h-16 text-white"
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
        </div>

        {/* Status text */}
        <p className="text-2xl font-heading font-semibold text-white drop-shadow-lg">
          {getStatusText()}
        </p>

        {/* Cancel button */}
        <button
          onClick={onCancel}
          className="
            px-8 py-3 rounded-full
            bg-white/20 hover:bg-white/30
            text-white font-body font-medium
            backdrop-blur-sm transition-all duration-200
            active:scale-95
          "
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
