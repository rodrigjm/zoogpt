/**
 * ErrorBoundary Component
 * Catches React errors and displays kid-friendly error message
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
    });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-leesburg-beige flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="text-6xl mb-4">🦁</div>
            <h1 className="text-2xl font-bold text-leesburg-brown mb-4">
              Oops! Something went wrong
            </h1>
            <p className="text-leesburg-brown/70 mb-6">
              Don't worry! Even the smartest animals make mistakes. Let's try again!
            </p>
            <button
              onClick={this.handleReset}
              className="bg-leesburg-green hover:bg-leesburg-green/90 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
            >
              Try Again
            </button>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="text-sm text-leesburg-brown/50 cursor-pointer">
                  Error Details (dev only)
                </summary>
                <pre className="mt-2 text-xs text-red-600 overflow-auto bg-red-50 p-2 rounded">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
