import React from 'react';
import { useVoiceStore } from '../../stores/voiceStore';

interface VoiceOverlayProps {
  onStop: () => void;
  onCancel: () => void;
}

export default function VoiceOverlay({ onStop, onCancel }: VoiceOverlayProps) {
  const mode = useVoiceStore((state) => state.mode);

  const isRecording = mode === 'recording';
  const isProcessing = mode === 'processing';

  const stopAriaLabel = isProcessing ? 'Processing audio' : 'Stop recording';
  const stopLabel = isProcessing ? 'Sending…' : 'Tap to Stop';

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-8">
        {/* Big interactive stop button (replaces the previously decorative mic) */}
        <button
          type="button"
          onClick={onStop}
          disabled={isProcessing}
          aria-label={stopAriaLabel}
          className={`
            relative w-32 h-32 rounded-full flex items-center justify-center
            ${isRecording ? 'bg-voice-recording animate-pulse-ring' : 'bg-voice-processing'}
            shadow-2xl active:scale-95 transition-transform duration-150
            disabled:cursor-not-allowed
          `}
        >
          {isProcessing ? (
            <svg
              className="w-16 h-16 text-white animate-spin"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
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
            // Stop-square glyph
            <span className="block w-12 h-12 rounded-md bg-white" aria-hidden="true" />
          )}
        </button>

        {/* Status / instruction text */}
        <p className="text-2xl font-heading font-semibold text-white drop-shadow-lg">
          {stopLabel}
        </p>

        {/* Secondary cancel pill */}
        <button
          onClick={onCancel}
          disabled={isProcessing}
          className="
            px-8 py-3 rounded-full
            bg-white/20 hover:bg-white/30
            text-white font-body font-medium
            backdrop-blur-sm transition-all duration-200
            active:scale-95 disabled:opacity-50
          "
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
