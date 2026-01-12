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
    </ErrorBoundary>
  );
}

export default App;
