import React from 'react';

export const TypingIndicator = React.memo(() => {
  return (
    <div className="flex gap-2 animate-message-in">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-sm">
        <svg className="w-5 h-5 text-white" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 2C5.6 2 2 5.6 2 10s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm-2 4.5a1 1 0 112 0 1 1 0 01-2 0zm4 0a1 1 0 112 0 1 1 0 01-2 0zM7 12.5c0-.3.2-.5.5-.5h5c.3 0 .5.2.5.5s-.2.5-.5.5h-5c-.3 0-.5-.2-.5-.5z"/>
        </svg>
      </div>

      {/* Typing bubble */}
      <div className="bg-bubble-assistant px-4 py-3 rounded-bubble rounded-bl-bubble-tail shadow-sm border border-accent-secondary/15">
        <div className="flex gap-1.5 items-center">
          <span
            className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-accent-secondary animate-typing-dot"
            style={{ animationDelay: '160ms' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-accent-teal animate-typing-dot"
            style={{ animationDelay: '320ms' }}
          />
        </div>
      </div>
    </div>
  );
});

TypingIndicator.displayName = 'TypingIndicator';
