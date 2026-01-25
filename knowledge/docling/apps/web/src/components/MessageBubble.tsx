import React, { memo } from 'react';
import type { ChatMessage, Source } from '../types';
import { AnimalImageGallery } from './index';

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

const MessageBubble: React.FC<MessageBubbleProps> = memo(({ message, isStreaming = false, sources }) => {
  const isUser = message.role === 'user';

  // Extract unique animals that have images
  const animalsWithImages = React.useMemo(() => {
    if (!sources || isStreaming) return [];

    const animalMap = new Map<string, Source>();
    sources.forEach(source => {
      if (source.image_urls && source.image_urls.length > 0) {
        // Only add if not already present (deduplication by animal name)
        if (!animalMap.has(source.animal)) {
          animalMap.set(source.animal, source);
        }
      }
    });

    return Array.from(animalMap.values());
  }, [sources, isStreaming]);

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        role="article"
        aria-label={`${isUser ? 'User' : 'Assistant'} message`}
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
        {!isStreaming && !isUser && animalsWithImages.length > 0 && (
          <div className="mt-4">
            {animalsWithImages.map((source) => (
              <AnimalImageGallery
                key={source.animal}
                animal={source.animal}
                images={source.image_urls!}
                thumbnail={source.thumbnail}
                alt={source.alt}
              />
            ))}
          </div>
        )}
        {sources && sources.length > 0 && !isUser && (
          <div className="mt-3 pt-3 border-t border-leesburg-brown/20">
            <p className="text-sm text-leesburg-brown/70 break-all">
              Sources:{' '}
              {[...new Set(sources.map(s => s.url).filter(Boolean))]
                .map((url, i, arr) => (
                  <span key={url}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-leesburg-orange hover:underline"
                    >
                      {url}
                    </a>
                    {i < arr.length - 1 && ', '}
                  </span>
                ))}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison: only re-render if props actually changed
  return (
    prevProps.message.content === nextProps.message.content &&
    prevProps.message.message_id === nextProps.message.message_id &&
    prevProps.isStreaming === nextProps.isStreaming &&
    prevProps.sources?.length === nextProps.sources?.length
  );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble;
