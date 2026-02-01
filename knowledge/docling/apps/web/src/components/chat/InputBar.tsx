import React, { useState, useRef, useEffect } from 'react';
import VoiceButton from './VoiceButton';
import SendButton from './SendButton';
import { useUIStore } from '../../stores/uiStore';

interface InputBarProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function InputBar({ onSend, disabled = false }: InputBarProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { setInputFocused } = useUIStore();

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = `${newHeight}px`;
  }, [message]);

  const handleSend = () => {
    if (!message.trim() || disabled) return;
    onSend(message.trim());
    setMessage('');
    // Reset height after send
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceTranscript = (text: string) => {
    // Auto-send voice transcripts for voice-first experience
    if (text.trim()) {
      onSend(text.trim());
    }
  };

  const hasText = message.trim().length > 0;

  return (
    <div className="flex items-end gap-2 p-4 bg-chat-canvas">
      {/* Text input container */}
      <div
        className="
          flex-1 bg-chat-surface rounded-full
          border border-black/10
          focus-within:border-accent-primary focus-within:ring-2 focus-within:ring-accent-primary/20
          transition-all duration-200
          px-4 py-2
        "
      >
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setInputFocused(true)}
          onBlur={() => setInputFocused(false)}
          disabled={disabled}
          placeholder="Ask about animals..."
          className="
            w-full resize-none bg-transparent
            text-base text-text-primary placeholder:text-text-muted
            outline-none border-none
            overflow-y-auto
          "
          style={{
            minHeight: '24px',
            maxHeight: '120px',
          }}
          rows={1}
        />
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        {hasText ? (
          <SendButton onClick={handleSend} disabled={disabled} />
        ) : (
          <VoiceButton onTranscript={handleVoiceTranscript} disabled={disabled} />
        )}
      </div>
    </div>
  );
}
