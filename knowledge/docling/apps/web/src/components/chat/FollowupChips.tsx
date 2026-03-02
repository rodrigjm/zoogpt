import React from 'react';

interface FollowupChipsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export default function FollowupChips({ questions, onSelect }: FollowupChipsProps) {
  if (questions.length === 0) return null;

  return (
    <div
      className="
        flex gap-2 overflow-x-auto pb-2
        scrollbar-hide snap-x snap-mandatory
      "
      style={{
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
      }}
    >
      {questions.map((question, index) => (
        <button
          key={index}
          onClick={() => onSelect(question)}
          className="
            flex-shrink-0 snap-start
            px-4 py-2 min-h-[44px]
            bg-chat-surface hover:bg-accent-teal
            text-text-primary hover:text-white
            border border-accent-secondary/25 hover:border-accent-teal
            rounded-full text-sm font-body
            transition-colors duration-200
            whitespace-nowrap cursor-pointer
            active:scale-95
          "
          type="button"
        >
          {question}
        </button>
      ))}
    </div>
  );
}
