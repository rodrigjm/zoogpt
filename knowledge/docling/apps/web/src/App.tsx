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
      {/* Park sign in top right corner */}
      <img
        src="/park-sign.jpg"
        alt="Leesburg Animal Park"
        className="fixed top-4 right-4 w-32 h-auto object-contain pointer-events-none z-50 rounded-lg shadow-lg"
      />
      {/* Mascot in bottom left corner */}
      <img
        src="/mascot.png"
        alt="Zoocari mascot"
        className="fixed bottom-0 left-0 w-[500px] h-auto object-contain pointer-events-none z-50"
      />
      {/* Macau on right side above monkey */}
      <img
        src="/macau.png"
        alt="Macau"
        className="fixed bottom-[400px] right-4 w-[300px] h-auto object-contain pointer-events-none z-50"
      />
    </ErrorBoundary>
  );
}

export default App;
