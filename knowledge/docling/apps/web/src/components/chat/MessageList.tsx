import React, { useEffect, useRef } from 'react';
import type { ChatMessage } from '../../types';
import { UserBubble } from './UserBubble';
import { AssistantBubble } from './AssistantBubble';
import { TypingIndicator } from './TypingIndicator';
import type { Source } from '../../types';

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  streamingContent?: string;
  sources?: Source[];
  onRate?: (messageId: string, rating: 'up' | 'down') => void;
  getRating?: (messageId: string) => 'up' | 'down' | null;
  onRequestImage?: (messageId: string) => void;
}

export const MessageList = React.memo<MessageListProps>(({
  messages,
  isStreaming = false,
  streamingContent = '',
  sources = [],
  onRate,
  getRating,
  onRequestImage,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamingContent, isStreaming]);

  // Group consecutive messages from same sender
  const groupedMessages: Array<{ role: string; messages: ChatMessage[] }> = [];

  messages.forEach((msg) => {
    const lastGroup = groupedMessages[groupedMessages.length - 1];
    if (lastGroup && lastGroup.role === msg.role) {
      lastGroup.messages.push(msg);
    } else {
      groupedMessages.push({ role: msg.role, messages: [msg] });
    }
  });

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-4 space-y-4 font-body"
    >
      {groupedMessages.map((group, groupIdx) => (
        <div
          key={groupIdx}
          className={group.role === 'user' ? 'space-y-2' : 'space-y-2'}
        >
          {group.messages.map((msg) => (
            <React.Fragment key={msg.message_id}>
              {msg.role === 'user' ? (
                <UserBubble
                  content={msg.content}
                  timestamp={msg.created_at ? new Date(msg.created_at) : undefined}
                />
              ) : (
                <AssistantBubble
                  id={msg.message_id}
                  content={msg.content}
                  sources={msg.sources}
                  timestamp={msg.created_at ? new Date(msg.created_at) : undefined}
                  onRate={onRate ? (rating) => onRate(msg.message_id, rating) : undefined}
                  currentRating={getRating?.(msg.message_id)}
                  onRequestImage={onRequestImage ? () => onRequestImage(msg.message_id) : undefined}
                  isImageOnly={msg.metadata?.isImageOnly === true}
                  imageUrls={(msg.metadata?.imageUrls as string[]) || []}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      ))}

      {/* Streaming message */}
      {isStreaming && streamingContent && (
        <AssistantBubble
          id="streaming"
          content={streamingContent}
          sources={sources}
        />
      )}

      {/* Typing indicator */}
      {isStreaming && !streamingContent && <TypingIndicator />}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
});

MessageList.displayName = 'MessageList';
