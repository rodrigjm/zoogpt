import React, { memo } from 'react';

interface FollowupQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

const FollowupQuestions: React.FC<FollowupQuestionsProps> = memo(({ questions, onSelect }) => {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="w-full px-4 py-3 mb-4">
      <p className="text-sm text-leesburg-brown font-medium mb-2 px-2">
        You might also like to ask:
      </p>
      <div
        role="group"
        aria-label="Follow-up question suggestions"
        className="flex flex-wrap gap-2"
      >
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onSelect(question)}
            aria-label={`Ask: ${question}`}
            className="
              px-4 py-2.5 min-h-11 rounded-full
              bg-leesburg-brown hover:bg-leesburg-orange
              text-white font-medium text-sm
              shadow-md hover:shadow-lg
              transition-all duration-200
              transform hover:scale-105 active:scale-95
              border-2 border-leesburg-brown border-opacity-20
              cursor-pointer
              focus:outline-none
              focus:ring-4
              focus:ring-leesburg-brown/30
            "
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
});

FollowupQuestions.displayName = 'FollowupQuestions';

export default FollowupQuestions;
