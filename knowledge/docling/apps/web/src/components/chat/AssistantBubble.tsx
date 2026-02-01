import React from 'react';
import type { Source } from '../../types';

interface AssistantBubbleProps {
  id: string;
  content: string;
  sources?: Source[];
  images?: string[];
  timestamp?: Date;
  onRate?: (rating: 'up' | 'down') => void;
  currentRating?: 'up' | 'down' | null;
  onRequestImage?: () => void;
  isImageOnly?: boolean;
  imageUrls?: string[];
}

export const AssistantBubble = React.memo<AssistantBubbleProps>(({
  id,
  content,
  sources = [],
  images = [],
  timestamp,
  onRate,
  currentRating,
  onRequestImage,
  isImageOnly = false,
  imageUrls = [],
}) => {
  const handleRating = (rating: 'up' | 'down') => {
    onRate?.(rating);
  };

  // Check if sources have available images
  const hasAvailableImages = sources.some(
    (source) => source.image_urls && source.image_urls.length > 0
  );

  // Image-only message rendering
  if (isImageOnly) {
    return (
      <div className="flex gap-2 animate-message-in">
        {/* Avatar */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white text-lg">
          🐘
        </div>

        <div className="flex flex-col gap-2 max-w-[85%]">
          {/* Message Bubble with images only */}
          <div className="bg-bubble-assistant text-bubble-assistant-text px-4 py-3 rounded-bubble rounded-bl-bubble-tail shadow-sm">
            <p className="text-base leading-relaxed whitespace-pre-wrap font-body mb-3">{content}</p>

            {/* Display images */}
            {imageUrls.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {imageUrls.map((img, idx) => (
                  <img
                    key={idx}
                    src={img}
                    alt={`Animal picture ${idx + 1}`}
                    className="rounded-lg max-w-full h-auto max-h-64 object-cover"
                    loading="lazy"
                  />
                ))}
              </div>
            )}

            {timestamp && (
              <time className="text-xs text-text-muted mt-2 block">
                {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </time>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-2 animate-message-in">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white text-lg">
        🐘
      </div>

      <div className="flex flex-col gap-2 max-w-[85%]">
        {/* Message Bubble */}
        <div className="bg-bubble-assistant text-bubble-assistant-text px-4 py-3 rounded-bubble rounded-bl-bubble-tail shadow-sm">
          <p className="text-base leading-relaxed whitespace-pre-wrap font-body">{content}</p>

          {timestamp && (
            <time className="text-xs text-text-muted mt-1 block">
              {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </time>
          )}

          {/* Images */}
          {images.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {images.map((img, idx) => (
                <img
                  key={idx}
                  src={img}
                  alt={`Response image ${idx + 1}`}
                  className="rounded-lg max-w-full h-auto"
                />
              ))}
            </div>
          )}

          {/* Sources (collapsible) */}
          {sources.length > 0 && (
            <details className="mt-3 text-text-secondary">
              <summary className="cursor-pointer text-sm font-medium hover:text-text-primary transition-colors">
                Sources ({sources.length})
              </summary>
              <ul className="mt-2 space-y-2 text-sm">
                {sources.map((source, idx) => (
                  <li key={idx} className="pl-3 border-l-2 border-accent-primary/30">
                    <div className="font-medium">{source.animal}</div>
                    <div className="text-text-muted">{source.title}</div>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent-primary hover:underline text-xs"
                      >
                        View source
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </details>
          )}

          {/* Want to see a picture? button */}
          {hasAvailableImages && onRequestImage && (
            <button
              onClick={onRequestImage}
              className="mt-3 px-4 py-2 min-h-[44px] bg-accent-secondary hover:bg-accent-secondary/80 text-text-primary rounded-full font-medium text-sm transition-all active:scale-95 flex items-center gap-2"
              type="button"
            >
              <span>Want to see a picture?</span>
            </button>
          )}
        </div>

        {/* Rating Buttons */}
        {onRate && (
          <div className="flex gap-2 ml-2">
            <button
              onClick={() => handleRating('up')}
              className={`text-lg transition-all ${
                currentRating === 'up'
                  ? 'text-accent-success scale-110'
                  : 'text-text-muted hover:text-accent-success hover:scale-110'
              }`}
              aria-label="Rate helpful"
              type="button"
            >
              👍
            </button>
            <button
              onClick={() => handleRating('down')}
              className={`text-lg transition-all ${
                currentRating === 'down'
                  ? 'text-accent-error scale-110'
                  : 'text-text-muted hover:text-accent-error hover:scale-110'
              }`}
              aria-label="Rate unhelpful"
              type="button"
            >
              👎
            </button>
          </div>
        )}
      </div>
    </div>
  );
});

AssistantBubble.displayName = 'AssistantBubble';
