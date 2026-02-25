import React, { memo } from 'react';

const WelcomeMessage = memo(() => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[150px] sm:min-h-[180px] md:min-h-[220px] px-3 sm:px-6 py-6 sm:py-8 md:py-12">
      <div className="max-w-2xl w-full text-center space-y-4 sm:space-y-6">
        {/* Main Welcome */}
        <div className="space-y-2 sm:space-y-3">
          <div className="flex items-center justify-center gap-3 sm:gap-4">
            <img
              src="/park-sign.jpg"
              alt="Leesburg Animal Park"
              className="w-10 h-10 sm:w-14 sm:h-14 md:w-16 md:h-16 lg:w-20 lg:h-20 object-contain rounded-lg"
            />
            <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-heading font-bold text-text-primary">
              Welcome to Zoocari @ Leesburg Animal Park
            </h2>
          </div>
        </div>

        {/* Description */}
        <div className="bg-chat-surface rounded-xl sm:rounded-2xl p-4 sm:p-6 border-2 border-accent-secondary/30">
          <p className="text-sm sm:text-base md:text-lg text-text-primary leading-relaxed">
            Ask me anything about the amazing animals at Leesburg Animal Park!
            I can tell you fun facts, what they eat, where they live, and much more.
          </p>
        </div>
      </div>
    </div>
  );
});

WelcomeMessage.displayName = 'WelcomeMessage';

export default WelcomeMessage;
