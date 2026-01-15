import React, { memo } from 'react';

const WelcomeMessage = memo(() => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[250px] sm:min-h-[300px] md:min-h-[400px] px-3 sm:px-6 py-6 sm:py-8 md:py-12">
      <div className="max-w-2xl w-full text-center space-y-4 sm:space-y-6">
        {/* Main Welcome */}
        <div className="space-y-2 sm:space-y-3">
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-leesburg-brown">
            Welcome to Zoocari! 🦁
          </h2>
          <p className="text-lg sm:text-xl md:text-2xl text-leesburg-orange font-medium">
            I'm your friendly zoo guide!
          </p>
        </div>

        {/* Description */}
        <div className="bg-leesburg-beige/50 rounded-xl sm:rounded-2xl p-4 sm:p-6 border-2 border-leesburg-yellow/30">
          <p className="text-sm sm:text-base md:text-lg text-leesburg-brown leading-relaxed">
            Ask me anything about the amazing animals at Leesburg Animal Park!
            I can tell you fun facts, what they eat, where they live, and much more.
          </p>
        </div>

        {/* Suggestions */}
        <div className="space-y-3 sm:space-y-4 mt-4 sm:mt-6 md:mt-8">
          <h3 className="text-base sm:text-lg md:text-xl font-semibold text-leesburg-brown flex items-center justify-center gap-2">
            <span>🎯</span>
            <span>Try asking me:</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 text-left">
            <div className="bg-white rounded-lg sm:rounded-xl p-3 sm:p-4 border-2 border-leesburg-blue/30 hover:border-leesburg-blue transition-colors">
              <p className="text-sm sm:text-base text-leesburg-brown font-medium">
                🦒 "Tell me about the giraffes"
              </p>
            </div>
            <div className="bg-white rounded-lg sm:rounded-xl p-3 sm:p-4 border-2 border-leesburg-orange/30 hover:border-leesburg-orange transition-colors">
              <p className="text-sm sm:text-base text-leesburg-brown font-medium">
                🐯 "What do tigers eat?"
              </p>
            </div>
            <div className="bg-white rounded-lg sm:rounded-xl p-3 sm:p-4 border-2 border-leesburg-yellow/30 hover:border-leesburg-yellow transition-colors">
              <p className="text-sm sm:text-base text-leesburg-brown font-medium">
                🦁 "How fast can a lion run?"
              </p>
            </div>
            <div className="bg-white rounded-lg sm:rounded-xl p-3 sm:p-4 border-2 border-leesburg-blue/30 hover:border-leesburg-blue transition-colors">
              <p className="text-sm sm:text-base text-leesburg-brown font-medium">
                🐘 "Where do elephants live?"
              </p>
            </div>
          </div>
        </div>

        {/* Getting Started Hint */}
        <div className="mt-4 sm:mt-6 md:mt-8 flex items-center justify-center gap-2 sm:gap-3 text-leesburg-brown/70">
          <span className="text-xl sm:text-2xl">👇</span>
          <p className="text-sm sm:text-base font-medium">
            Choose an animal below or start chatting!
          </p>
        </div>
      </div>
    </div>
  );
});

WelcomeMessage.displayName = 'WelcomeMessage';

export default WelcomeMessage;
