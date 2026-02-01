/**
 * ModeToggle - Pill-style toggle between voice and text input modes
 * Uses uiStore for state management
 */

import React from 'react';
import { useUIStore } from '../../stores/uiStore';

export const ModeToggle: React.FC = () => {
  const inputMode = useUIStore((state) => state.inputMode);
  const toggleInputMode = useUIStore((state) => state.toggleInputMode);

  return (
    <div className="inline-flex bg-chat-surface rounded-full p-1">
      {/* Voice mode button */}
      <button
        type="button"
        onClick={() => inputMode !== 'voice' && toggleInputMode()}
        className={`
          min-h-[44px] min-w-[44px] px-4 py-2 rounded-full
          flex items-center gap-2 transition-all duration-200
          ${
            inputMode === 'voice'
              ? 'bg-accent-primary text-white shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          }
        `}
        aria-label="Voice mode"
        aria-pressed={inputMode === 'voice'}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-5 h-5"
        >
          <path d="M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0V4.5Z" />
          <path d="M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.751 6.751 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.751 6.751 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5Z" />
        </svg>
        <span className="text-sm font-medium hidden sm:inline">Voice</span>
      </button>

      {/* Text mode button */}
      <button
        type="button"
        onClick={() => inputMode !== 'text' && toggleInputMode()}
        className={`
          min-h-[44px] min-w-[44px] px-4 py-2 rounded-full
          flex items-center gap-2 transition-all duration-200
          ${
            inputMode === 'text'
              ? 'bg-accent-primary text-white shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          }
        `}
        aria-label="Text mode"
        aria-pressed={inputMode === 'text'}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-5 h-5"
        >
          <path d="M21.731 2.269a2.625 2.625 0 0 0-3.712 0l-1.157 1.157 3.712 3.712 1.157-1.157a2.625 2.625 0 0 0 0-3.712ZM19.513 8.199l-3.712-3.712-8.4 8.4a5.25 5.25 0 0 0-1.32 2.214l-.8 2.685a.75.75 0 0 0 .933.933l2.685-.8a5.25 5.25 0 0 0 2.214-1.32l8.4-8.4Z" />
          <path d="M5.25 5.25a3 3 0 0 0-3 3v10.5a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3V13.5a.75.75 0 0 0-1.5 0v5.25a1.5 1.5 0 0 1-1.5 1.5H5.25a1.5 1.5 0 0 1-1.5-1.5V8.25a1.5 1.5 0 0 1 1.5-1.5h5.25a.75.75 0 0 0 0-1.5H5.25Z" />
        </svg>
        <span className="text-sm font-medium hidden sm:inline">Text</span>
      </button>
    </div>
  );
};
