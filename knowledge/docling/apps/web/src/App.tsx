/**
 * Zoocari App - Main Application
 * Mobile-first chat interface with Leesburg Animal Park branding
 */

import ErrorBoundary from './components/ErrorBoundary';
import NewChatInterface from './components/ChatInterface/NewChatInterface';

function App() {
  return (
    <ErrorBoundary>
      <NewChatInterface />
      {/* Park sign - only visible xl+, scales with viewport */}
      <img
        src="/park-sign.jpg"
        alt="Leesburg Animal Park"
        className="hidden xl:block fixed top-4 right-4 w-[6vw] min-w-[60px] max-w-[120px] h-auto object-contain pointer-events-none z-10 opacity-40 rounded-lg shadow-lg"
      />
      {/* Mascot - only visible xl+, scales with viewport */}
      <img
        src="/mascot.png"
        alt="Zoocari mascot"
        className="hidden xl:block fixed bottom-0 left-0 w-[12vw] min-w-[100px] max-w-[250px] h-auto object-contain pointer-events-none z-10 opacity-40"
      />
      {/* Macaw - only visible 2xl+, scales with viewport */}
      <img
        src="/macau.png"
        alt="Macaw"
        className="hidden 2xl:block fixed bottom-[20vh] right-4 w-[8vw] min-w-[80px] max-w-[160px] h-auto object-contain pointer-events-none z-10 opacity-40"
      />
    </ErrorBoundary>
  );
}

export default App;
