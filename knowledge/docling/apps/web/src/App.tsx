/**
 * Zoocari App - Main Application
 * Integrates Layout, ChatInterface, and ErrorBoundary
 */

import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <ChatInterface />
      </Layout>
      {/* Park sign in top right corner - hidden on mobile, visible on tablet+ */}
      <img
        src="/park-sign.jpg"
        alt="Leesburg Animal Park"
        className="hidden md:block fixed top-4 right-4 w-24 lg:w-32 h-auto object-contain pointer-events-none z-50 rounded-lg shadow-lg"
      />
      {/* Mascot in bottom left corner - hidden on mobile/tablet, visible on large screens */}
      <img
        src="/mascot.png"
        alt="Zoocari mascot"
        className="hidden lg:block fixed bottom-0 left-0 w-[300px] xl:w-[400px] 2xl:w-[500px] h-auto object-contain pointer-events-none z-50"
      />
      {/* Macaw on right side - hidden on mobile/tablet, visible on large screens */}
      <img
        src="/macau.png"
        alt="Macaw"
        className="hidden lg:block fixed bottom-[200px] xl:bottom-[300px] 2xl:bottom-[400px] right-4 w-[150px] xl:w-[200px] 2xl:w-[300px] h-auto object-contain pointer-events-none z-50"
      />
    </ErrorBoundary>
  );
}

export default App;
