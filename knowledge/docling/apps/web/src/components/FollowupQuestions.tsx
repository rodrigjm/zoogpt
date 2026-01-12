import React from 'react';

interface FollowupQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

const FollowupQuestions: React.FC<FollowupQuestionsProps> = ({ questions, onSelect }) => {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="w-full px-4 py-3 mb-4">
      <p className="text-sm text-leesburg-brown font-medium mb-2 px-2">
        You might also like to ask:
      </p>
      <div className="flex flex-wrap gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onSelect(question)}
            className="
              px-4 py-2.5 rounded-full
              bg-leesburg-brown hover:bg-leesburg-orange
              text-white font-medium text-sm
              shadow-md hover:shadow-lg
              transition-all duration-200
              transform hover:scale-105 active:scale-95
              border-2 border-leesburg-brown border-opacity-20
              cursor-pointer
            "
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
};

export default FollowupQuestions;
