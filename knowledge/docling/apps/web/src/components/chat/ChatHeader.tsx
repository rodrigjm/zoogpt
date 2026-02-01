/**
 * ChatHeader - Fixed header with branding and mode toggle
 * 56px height with safe area padding
 */

import React from 'react';
import { ModeToggle } from './ModeToggle';

export const ChatHeader: React.FC = () => {
  return (
    <header className="h-14 bg-chat-elevated border-b border-black/5 px-4 flex items-center justify-between shadow-sm pt-[env(safe-area-inset-top)]">
      {/* Branding */}
      <div className="flex items-center gap-2">
        <span className="text-2xl" role="img" aria-label="elephant">
          🐘
        </span>
        <h1 className="font-heading font-bold text-xl text-text-primary">
          Zoocari
        </h1>
      </div>

      {/* Mode toggle */}
      <ModeToggle />
    </header>
  );
};
