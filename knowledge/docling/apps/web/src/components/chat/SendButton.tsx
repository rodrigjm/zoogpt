import React from 'react';

interface SendButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export default function SendButton({ onClick, disabled = false }: SendButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="
        w-12 h-12 rounded-full flex items-center justify-center
        bg-accent-teal hover:bg-accent-teal-hover
        shadow-md transition-all duration-200 cursor-pointer
        active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed
      "
      aria-label="Send message"
      type="button"
    >
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
        />
      </svg>
    </button>
  );
}
