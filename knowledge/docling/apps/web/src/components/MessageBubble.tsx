import React from 'react';
import type { ChatMessage, Source } from '../types';

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  sources?: Source[];
}

const StreamingIndicator: React.FC = () => (
  <div className="flex items-center space-x-1 py-1">
    <div className="w-2 h-2 bg-leesburg-orange rounded-full animate-bounce [animation-delay:-0.3s]"></div>
    <div className="w-2 h-2 bg-leesburg-orange rounded-full animate-bounce [animation-delay:-0.15s]"></div>
    <div className="w-2 h-2 bg-leesburg-orange rounded-full animate-bounce"></div>
  </div>
);

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isStreaming = false, sources }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`
          max-w-[75%] px-6 py-4 rounded-3xl shadow-md
          ${isUser
            ? 'bg-leesburg-yellow text-leesburg-brown rounded-br-md'
            : 'bg-leesburg-beige text-leesburg-brown rounded-bl-md'
          }
        `}
      >
        <p className="text-lg leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </p>
        {isStreaming && !isUser && (
          <StreamingIndicator />
        )}
        {sources && sources.length > 0 && !isUser && (
          <div className="mt-3 pt-3 border-t border-leesburg-brown/20">
            <p className="text-sm text-leesburg-brown/70">
              Sources: {sources.map(s => `${s.animal} - ${s.title}`).join(', ')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
