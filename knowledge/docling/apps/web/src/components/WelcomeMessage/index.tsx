import React, { memo } from 'react';

const WelcomeMessage = memo(() => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[150px] sm:min-h-[180px] md:min-h-[220px] px-3 sm:px-6 py-6 sm:py-8 md:py-12">
      <div className="max-w-2xl w-full text-center space-y-4 sm:space-y-6">
        {/* Main Welcome */}
        <div className="space-y-2 sm:space-y-3">
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-heading font-bold text-text-primary">
            Welcome to Zoocari! 🦁
          </h2>
          <p className="text-lg sm:text-xl md:text-2xl text-text-secondary font-medium">
            I'm your friendly zoo guide!
          </p>
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
