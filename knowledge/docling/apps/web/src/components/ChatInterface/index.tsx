import React, { useState, useEffect, useRef, lazy, Suspense, useCallback } from 'react';
import { useSessionStore, useChatStore } from '../../stores';
import { textToSpeech, submitSurvey } from '../../lib/api';
import VoiceButton from '../VoiceButton';
import ChatInput from '../ChatInput';
import MessageBubble from '../MessageBubble';
import AnimalGrid from '../AnimalGrid';
import FollowupQuestions from '../FollowupQuestions';
import WelcomeMessage from '../WelcomeMessage';

// Lazy load AudioPlayer since it's only needed when TTS is available
const AudioPlayer = lazy(() => import('../AudioPlayer'));

type InputMode = 'voice' | 'text';

export default function ChatInterface() {
  const [inputMode, setInputMode] = useState<InputMode>('voice');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [hasThumbsDown, setHasThumbsDown] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Store state
  const { sessionId, initSession, isLoading: sessionLoading } = useSessionStore();
  const {
    messages,
    isStreaming,
    streamingContent,
    sources,
    followupQuestions,
    error,
    sendMessageStream,
  } = useChatStore();

  // Initialize or validate session on mount
  // Always call initSession - it handles both new sessions and validating cached ones
  useEffect(() => {
    initSession('web').catch((err) => {
      console.error('Failed to initialize session:', err);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount

  // Auto-scroll to bottom on new messages or streaming content
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Generate TTS for new assistant messages
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (
      lastMessage &&
      lastMessage.role === 'assistant' &&
      sessionId &&
      !isStreaming
    ) {
      // Generate TTS
      textToSpeech({
        session_id: sessionId,
        text: lastMessage.content,
        voice: 'af_heart', // Default voice for kids
      })
        .then((blob) => {
          setAudioBlob(blob);
        })
        .catch((err) => {
          console.error('TTS generation failed:', err);
        });
    }
  }, [messages, sessionId, isStreaming]);

  // Handle text input send
  const handleTextSend = useCallback((text: string) => {
    if (!sessionId || !text.trim()) return;
    sendMessageStream(sessionId, text.trim());
  }, [sessionId, sendMessageStream]);

  // Handle voice transcript
  const handleVoiceTranscript = useCallback((transcript: string) => {
    if (!sessionId || !transcript?.trim()) return;
    sendMessageStream(sessionId, transcript.trim());
  }, [sessionId, sendMessageStream]);

  // Handle followup question click
  const handleFollowupClick = useCallback((question: string) => {
    if (!sessionId) return;
    sendMessageStream(sessionId, question);
  }, [sessionId, sendMessageStream]);

  // Handle animal selection
  const handleAnimalSelect = useCallback((animal: string) => {
    if (!sessionId) return;
    const message = `Tell me about the ${animal}`;
    sendMessageStream(sessionId, message);
  }, [sessionId, sendMessageStream]);

  // Handle mode toggle
  const toggleMode = useCallback(() => {
    setInputMode((prev) => (prev === 'voice' ? 'text' : 'voice'));
  }, []);

  // Handle rating change
  const handleRatingChange = useCallback((messageId: string, rating: 'up' | 'down') => {
    if (rating === 'down') {
      setHasThumbsDown(true);
    }
  }, []);

  // Handle feedback modal submit
  const handleFeedbackSubmit = useCallback(async () => {
    if (!sessionId || !feedbackText.trim()) return;

    try {
      await submitSurvey(sessionId, feedbackText.trim());
      setFeedbackSubmitted(true);
      setFeedbackText('');
      setTimeout(() => {
        setShowFeedbackModal(false);
        setFeedbackSubmitted(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  }, [sessionId, feedbackText]);

  // Check if interaction is disabled
  const isDisabled = sessionLoading || isStreaming || !sessionId;

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto">
      {/* Header with Mode Toggle */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 bg-white shadow-sm border-b-2 border-leesburg-beige">
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-leesburg-brown">
          Zoocari Chat
        </h1>
        <button
          onClick={toggleMode}
          disabled={isDisabled}
          className={`
            px-3 sm:px-4 py-2 rounded-full font-medium text-xs sm:text-sm
            transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-leesburg-blue/30
            ${
              isDisabled
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-leesburg-blue hover:bg-blue-500 text-white active:scale-95'
            }
          `}
          aria-label={`Switch to ${inputMode === 'voice' ? 'text' : 'voice'} mode`}
        >
          {inputMode === 'voice' ? '💬 Text Mode' : '🎤 Voice Mode'}
        </button>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-3 sm:py-4 bg-gradient-to-b from-leesburg-beige/20 to-white">
        {/* Show welcome message and animal grid if no messages */}
        {messages.length === 0 && !isStreaming && (
          <>
            <WelcomeMessage />
            <AnimalGrid
              onSelectAnimal={handleAnimalSelect}
              disabled={isDisabled}
            />
          </>
        )}

        {/* Message List */}
        <div
          className="space-y-4"
          role="log"
          aria-live="polite"
          aria-label="Chat messages"
        >
          {messages.map((msg) => (
            <MessageBubble
              key={msg.message_id}
              message={msg}
              sources={msg.role === 'assistant' ? sources : undefined}
              onRatingChange={handleRatingChange}
            />
          ))}

          {/* Streaming message bubble */}
          {isStreaming && streamingContent && (
            <MessageBubble
              message={{
                message_id: 'streaming',
                session_id: sessionId || '',
                role: 'assistant',
                content: streamingContent,
                created_at: new Date().toISOString(),
              }}
              isStreaming={true}
            />
          )}

          {/* Error message */}
          {error && (
            <div className="flex justify-center" role="alert" aria-live="assertive">
              <div className="px-6 py-3 bg-red-100 border-2 border-red-400 text-red-700 rounded-xl max-w-lg">
                <p className="font-medium">Error:</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Follow-up Questions */}
      {followupQuestions.length > 0 && !isStreaming && (
        <FollowupQuestions
          questions={followupQuestions}
          onSelect={handleFollowupClick}
        />
      )}

      {/* Audio Player */}
      {audioBlob && (
        <div className="px-4 sm:px-6 py-2 sm:py-3">
          <Suspense fallback={<div className="text-center text-gray-500">Loading audio player...</div>}>
            <AudioPlayer audioBlob={audioBlob} autoPlay={true} />
          </Suspense>
        </div>
      )}

      {/* Feedback Link */}
      {messages.length > 0 && (
        <div className="px-4 sm:px-6 py-2 text-center border-t border-leesburg-beige/50">
          <button
            onClick={() => setShowFeedbackModal(true)}
            className={`text-sm text-leesburg-brown/60 hover:text-leesburg-brown transition-colors ${
              hasThumbsDown ? 'animate-pulse' : ''
            }`}
          >
            Share your thoughts
          </button>
        </div>
      )}

      {/* Input Area */}
      <div className="px-4 sm:px-6 py-3 sm:py-4 bg-white border-t-2 border-leesburg-beige">
        {inputMode === 'voice' && sessionId ? (
          <div className="flex justify-center py-4">
            <VoiceButton
              sessionId={sessionId}
              onTranscript={handleVoiceTranscript}
              disabled={isDisabled}
            />
          </div>
        ) : (
          <ChatInput
            onSend={handleTextSend}
            onMicClick={toggleMode}
            disabled={isDisabled}
            placeholder="Ask me about the animals..."
          />
        )}
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowFeedbackModal(false)}
        >
          <div
            className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-leesburg-brown">Share Your Feedback</h2>
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            {feedbackSubmitted ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-2">✅</div>
                <p className="text-leesburg-brown font-medium">Thank you for your feedback!</p>
              </div>
            ) : (
              <>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Tell us what you think..."
                  maxLength={2000}
                  className="w-full h-32 px-4 py-3 border-2 border-leesburg-beige rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-leesburg-blue/50 text-leesburg-brown"
                />
                <div className="flex justify-between items-center mt-4">
                  <span className="text-sm text-gray-500">
                    {feedbackText.length} / 2000
                  </span>
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={!feedbackText.trim()}
                    className={`px-6 py-2 rounded-full font-medium transition-all ${
                      feedbackText.trim()
                        ? 'bg-leesburg-blue text-white hover:bg-blue-500 active:scale-95'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    Submit
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
