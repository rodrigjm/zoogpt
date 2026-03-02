/**
 * ChatHeader - Fixed header with warm safari gradient and mode toggle
 * 56px height with safe area padding
 */

import React from 'react';
import { ModeToggle } from './ModeToggle';

export const ChatHeader: React.FC = () => {
  return (
    <header className="h-14 bg-gradient-to-r from-accent-primary via-accent-secondary to-accent-primary px-4 flex items-center justify-between shadow-md pt-[env(safe-area-inset-top)]">
      {/* Branding */}
      <div className="flex items-center gap-2">
        <div className="w-9 h-9 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-sm">
          <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.5 10c-.4-2.1-2.3-4-4.5-4.5V4c0-.6-.4-1-1-1h-4c-.6 0-1 .4-1 1v1.5C6.8 6 4.9 7.9 4.5 10H3c-.6 0-1 .4-1 1v2c0 .6.4 1 1 1h1.5c.5 2.6 3 4.5 5.5 4.9V21c0 .6.4 1 1 1h2c.6 0 1-.4 1-1v-2.1c2.5-.4 5-2.3 5.5-4.9H21c.6 0 1-.4 1-1v-2c0-.6-.4-1-1-1h-1.5zM12 16c-2.2 0-4-1.8-4-4s1.8-4 4-4 4 1.8 4 4-1.8 4-4 4z"/>
          </svg>
        </div>
        <h1 className="font-heading font-bold text-xl text-white drop-shadow-sm tracking-wide">
          Zoocari
        </h1>
      </div>

      {/* Mode toggle */}
      <ModeToggle />
    </header>
  );
};
