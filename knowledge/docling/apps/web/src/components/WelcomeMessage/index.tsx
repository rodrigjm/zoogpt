import React, { memo } from 'react';

const WelcomeMessage = memo(() => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] px-6 py-12">
      <div className="max-w-2xl w-full text-center space-y-6">
        {/* Main Welcome */}
        <div className="space-y-3">
          <h2 className="text-5xl font-bold text-leesburg-brown">
            Welcome to Zoocari! 🦁
          </h2>
          <p className="text-2xl text-leesburg-orange font-medium">
            I'm your friendly zoo guide!
          </p>
        </div>

        {/* Description */}
        <div className="bg-leesburg-beige/50 rounded-2xl p-6 border-2 border-leesburg-yellow/30">
          <p className="text-lg text-leesburg-brown leading-relaxed">
            Ask me anything about the amazing animals at Leesburg Animal Park!
            I can tell you fun facts, what they eat, where they live, and much more.
          </p>
        </div>

        {/* Suggestions */}
        <div className="space-y-4 mt-8">
          <h3 className="text-xl font-semibold text-leesburg-brown flex items-center justify-center gap-2">
            <span>🎯</span>
            <span>Try asking me:</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
            <div className="bg-white rounded-xl p-4 border-2 border-leesburg-blue/30 hover:border-leesburg-blue transition-colors">
              <p className="text-leesburg-brown font-medium">
                🦒 "Tell me about the giraffes"
              </p>
            </div>
            <div className="bg-white rounded-xl p-4 border-2 border-leesburg-orange/30 hover:border-leesburg-orange transition-colors">
              <p className="text-leesburg-brown font-medium">
                🐯 "What do tigers eat?"
              </p>
            </div>
            <div className="bg-white rounded-xl p-4 border-2 border-leesburg-yellow/30 hover:border-leesburg-yellow transition-colors">
              <p className="text-leesburg-brown font-medium">
                🦁 "How fast can a lion run?"
              </p>
            </div>
            <div className="bg-white rounded-xl p-4 border-2 border-leesburg-blue/30 hover:border-leesburg-blue transition-colors">
              <p className="text-leesburg-brown font-medium">
                🐘 "Where do elephants live?"
              </p>
            </div>
          </div>
        </div>

        {/* Getting Started Hint */}
        <div className="mt-8 flex items-center justify-center gap-3 text-leesburg-brown/70">
          <span className="text-2xl">👇</span>
          <p className="text-base font-medium">
            Choose an animal below or start chatting!
          </p>
        </div>
      </div>
    </div>
  );
});

WelcomeMessage.displayName = 'WelcomeMessage';

export default WelcomeMessage;
