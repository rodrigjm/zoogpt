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
    </ErrorBoundary>
  );
}

export default App;
