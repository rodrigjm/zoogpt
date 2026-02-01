import React from 'react';

export const TypingIndicator = React.memo(() => {
  return (
    <div className="flex gap-2 animate-message-in">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white text-lg">
        🐘
      </div>

      {/* Typing bubble */}
      <div className="bg-bubble-assistant px-4 py-3 rounded-bubble rounded-bl-bubble-tail shadow-sm">
        <div className="flex gap-1 items-center">
          <span
            className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot"
            style={{ animationDelay: '160ms' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot"
            style={{ animationDelay: '320ms' }}
          />
        </div>
      </div>
    </div>
  );
});

TypingIndicator.displayName = 'TypingIndicator';
