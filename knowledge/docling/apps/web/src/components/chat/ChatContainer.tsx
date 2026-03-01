/**
 * ChatContainer - Main layout wrapper for chat UI
 * Provides full viewport height with sticky header and footer
 */

import React, { type ReactNode } from 'react';

interface ChatContainerProps {
  header: ReactNode;
  footer: ReactNode;
  children: ReactNode;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  header,
  footer,
  children,
}) => {
  return (
    <div className="flex flex-col h-[100dvh] bg-chat-canvas font-body text-text-primary">
      {/* Sticky header */}
      <div className="sticky top-0 z-10">{header}</div>

      {/* Scrollable main content area */}
      <main className="flex-1 overflow-y-auto overscroll-contain px-4 py-4 scroll-smooth">
        {children}
      </main>

      {/* Sticky footer with safe area padding */}
      <footer className="sticky bottom-0 bg-chat-canvas border-t border-accent-secondary/15 pb-[env(safe-area-inset-bottom)]">
        {footer}
      </footer>
    </div>
  );
};
