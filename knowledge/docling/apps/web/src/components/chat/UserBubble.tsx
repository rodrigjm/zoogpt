import React from 'react';

interface UserBubbleProps {
  content: string;
  timestamp?: Date;
}

export const UserBubble = React.memo<UserBubbleProps>(({ content, timestamp }) => {
  return (
    <div className="flex justify-end animate-message-in">
      <div className="max-w-[85%] bg-gradient-to-br from-bubble-user to-accent-primary-hover text-bubble-user-text px-4 py-3 rounded-bubble rounded-br-bubble-tail shadow-sm">
        <p className="text-base leading-relaxed whitespace-pre-wrap font-body">{content}</p>
        {timestamp && (
          <time className="text-xs text-bubble-user-text/70 mt-1 block">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </time>
        )}
      </div>
    </div>
  );
});

UserBubble.displayName = 'UserBubble';
