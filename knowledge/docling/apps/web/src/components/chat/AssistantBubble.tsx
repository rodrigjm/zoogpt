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
  onFeedback?: () => void;
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
  onFeedback,
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

  // Avatar component - reusable
  const Avatar = () => (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-sm">
      <svg className="w-5 h-5 text-white" viewBox="0 0 20 20" fill="currentColor">
        <path d="M10 2C5.6 2 2 5.6 2 10s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm-2 4.5a1 1 0 112 0 1 1 0 01-2 0zm4 0a1 1 0 112 0 1 1 0 01-2 0zM7 12.5c0-.3.2-.5.5-.5h5c.3 0 .5.2.5.5s-.2.5-.5.5h-5c-.3 0-.5-.2-.5-.5z"/>
      </svg>
    </div>
  );

  // Image-only message rendering
  if (isImageOnly) {
    return (
      <div className="flex gap-2 animate-message-in">
        <Avatar />
        <div className="flex flex-col gap-2 max-w-[85%]">
          <div className="bg-bubble-assistant text-bubble-assistant-text px-4 py-3 rounded-bubble rounded-bl-bubble-tail shadow-sm border border-accent-secondary/15">
            <p className="text-base leading-relaxed whitespace-pre-wrap font-body mb-3">{content}</p>

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
      <Avatar />

      <div className="flex flex-col gap-2 max-w-[85%]">
        {/* Message Bubble */}
        <div className="bg-bubble-assistant text-bubble-assistant-text px-4 py-3 rounded-bubble rounded-bl-bubble-tail shadow-sm border border-accent-secondary/15">
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
          {sources.length > 0 && (() => {
            const uniqueSources = sources.filter((s, i, arr) => arr.findIndex(x => x.animal === s.animal && x.title === s.title) === i);
            return (
            <details className="mt-3 text-text-secondary">
              <summary className="cursor-pointer text-sm font-medium hover:text-accent-primary transition-colors">
                Sources ({uniqueSources.length})
              </summary>
              <ul className="mt-2 space-y-2 text-sm">
                {uniqueSources.map((source) => (
                  <li key={`${source.animal}-${source.title}`} className="pl-3 border-l-2 border-accent-secondary/40">
                    <div className="font-medium">{source.animal}</div>
                    <div className="text-text-muted">{source.title}</div>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent-teal hover:underline text-xs"
                      >
                        View source
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </details>
            );
          })()}

          {/* Gallery disabled — images incorrect for ~60/70 animals. See backlog in ProjectPlan.md
          {hasAvailableImages && onRequestImage && (
            <button
              onClick={onRequestImage}
              className="mt-3 px-4 py-2 min-h-[44px] bg-accent-secondary hover:bg-accent-secondary/80 text-text-primary rounded-full font-medium text-sm transition-all active:scale-95 flex items-center gap-2"
              type="button"
            >
              <span>Want to see a picture?</span>
            </button>
          )}
          */}
        </div>

        {/* Rating Buttons */}
        {onRate && (
          <div className="flex gap-2 ml-2">
            <button
              onClick={() => handleRating('up')}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                currentRating === 'up'
                  ? 'bg-accent-teal/15 text-accent-teal scale-110'
                  : 'text-text-muted hover:text-accent-teal hover:bg-accent-teal/10 hover:scale-110'
              }`}
              aria-label="Rate helpful"
              type="button"
            >
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z"/>
              </svg>
            </button>
            <button
              onClick={() => handleRating('down')}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                currentRating === 'down'
                  ? 'bg-accent-error/15 text-accent-error scale-110'
                  : 'text-text-muted hover:text-accent-error hover:bg-accent-error/10 hover:scale-110'
              }`}
              aria-label="Rate unhelpful"
              type="button"
            >
              <svg className="w-4 h-4 rotate-180" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z"/>
              </svg>
            </button>
            {onFeedback && (
              <button
                onClick={onFeedback}
                className="text-xs text-text-muted hover:text-text-secondary transition-colors ml-1 cursor-pointer"
                type="button"
              >
                Share your thoughts
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

AssistantBubble.displayName = 'AssistantBubble';
