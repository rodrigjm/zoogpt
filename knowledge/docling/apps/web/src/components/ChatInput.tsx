import React, { useState, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (text: string) => void;
  onMicClick: () => void;
  disabled?: boolean;
  isRecording?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onMicClick,
  disabled = false,
  isRecording = false,
  placeholder = 'Ask me about the animals...',
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !disabled) {
      handleSend();
    }
  };

  return (
    <div className="flex items-center gap-3 p-4 bg-white rounded-2xl shadow-lg border-2 border-leesburg-beige">
      {/* Voice-first: Prominent microphone button */}
      <button
        onClick={onMicClick}
        disabled={disabled}
        className={`
          flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center
          transition-all duration-200 focus:outline-none focus:ring-4
          ${
            isRecording
              ? 'bg-red-500 animate-pulse shadow-lg shadow-red-300 focus:ring-red-300'
              : disabled
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-leesburg-orange hover:bg-orange-600 focus:ring-leesburg-orange/30 active:scale-95'
          }
        `}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        <svg
          className="w-8 h-8 text-white"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          {isRecording ? (
            <rect x="6" y="6" width="12" height="12" rx="2" />
          ) : (
            <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 14 0h-2zm-4 5.91V19h2a1 1 0 0 1 0 2H9a1 1 0 0 1 0-2h2v-2.09A7 7 0 0 1 5 11a1 1 0 0 1 2 0 5 5 0 0 0 10 0 1 1 0 0 1 2 0 7 7 0 0 1-6 6.91z" />
          )}
        </svg>
      </button>

      {/* Text input field */}
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={disabled}
        placeholder={placeholder}
        className={`
          flex-1 px-4 py-3 text-lg rounded-xl border-2 border-transparent
          bg-leesburg-beige text-leesburg-brown placeholder-gray-500
          focus:outline-none focus:border-leesburg-orange focus:bg-white
          transition-all duration-200
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        aria-label="Chat message input"
      />

      {/* Send button */}
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className={`
          flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center
          transition-all duration-200 focus:outline-none focus:ring-4
          ${
            disabled || !input.trim()
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-leesburg-blue hover:bg-blue-500 focus:ring-leesburg-blue/30 active:scale-95'
          }
        `}
        aria-label="Send message"
      >
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>
    </div>
  );
};

export default ChatInput;
