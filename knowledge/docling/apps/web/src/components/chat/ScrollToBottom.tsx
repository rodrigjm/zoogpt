/**
 * ScrollToBottom - Floating action button for quick scroll to bottom
 * Appears when user has scrolled up in the message list
 */

import React from 'react';

interface ScrollToBottomProps {
  onClick: () => void;
}

export const ScrollToBottom: React.FC<ScrollToBottomProps> = ({ onClick }) => {

  return (
    <button
      type="button"
      onClick={onClick}
      className="
        fixed bottom-24 right-4 z-20
        min-h-[44px] min-w-[44px]
        bg-accent-teal text-white
        rounded-full shadow-lg
        flex items-center justify-center
        hover:bg-accent-teal-hover cursor-pointer
        active:scale-95
        transition-all duration-200
        animate-message-in
      "
      aria-label="Scroll to bottom"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="currentColor"
        className="w-6 h-6"
      >
        <path
          fillRule="evenodd"
          d="M12 2.25a.75.75 0 0 1 .75.75v16.19l6.22-6.22a.75.75 0 1 1 1.06 1.06l-7.5 7.5a.75.75 0 0 1-1.06 0l-7.5-7.5a.75.75 0 1 1 1.06-1.06l6.22 6.22V3a.75.75 0 0 1 .75-.75Z"
          clipRule="evenodd"
        />
      </svg>
    </button>
  );
};
