/**
 * NewChatInterface - Redesigned mobile-first chat UI
 * Phase 3 integration of all new chat components
 */

import React, { useEffect, useCallback, lazy, Suspense, useRef, useState } from 'react';
import { useSessionStore, useChatStore } from '../../stores';
import { useUIStore } from '../../stores/uiStore';
import { useVoiceStore } from '../../stores/voiceStore';
import { submitSurvey } from '../../lib/api';
import type { TtsStreamAudioChunk } from '../../types';

// New chat components
import { ChatContainer, ChatHeader, ScrollToBottom } from '../chat';
import { MessageList } from '../chat/MessageList';
import InputBar from '../chat/InputBar';
import FollowupChips from '../chat/FollowupChips';
import VoiceOverlay from '../chat/VoiceOverlay';

// Existing components
import WelcomeMessage from '../WelcomeMessage';
import AnimalGrid from '../AnimalGrid';

// Lazy load AudioPlayer
const AudioPlayer = lazy(() => import('../AudioPlayer'));

export default function NewChatInterface() {
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Store state
  const { sessionId, initSession, isLoading: sessionLoading } = useSessionStore();
  const {
    messages,
    isStreaming,
    streamingContent,
    sources,
    followupQuestions,
    error,
    sendMessagePipelined,
    setRating,
    getRating,
    addImageMessage,
  } = useChatStore();

  const { inputMode, showJumpToBottom, setShowJumpToBottom } = useUIStore();
  const { mode: voiceMode } = useVoiceStore();

  // Initialize session on mount
  useEffect(() => {
    initSession('web').catch((err) => {
      console.error('Failed to initialize session:', err);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Audio queue for pipelined TTS playback
  const audioQueueRef = useRef<Blob[]>([]);
  const isPlayingRef = useRef(false);

  const playNextChunk = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsAudioPlaying(false);
      return;
    }

    isPlayingRef.current = true;
    setIsAudioPlaying(true);
    const blob = audioQueueRef.current.shift()!;
    setAudioBlob(blob);
  }, []);

  const handleAudioChunk = useCallback((chunk: TtsStreamAudioChunk) => {
    // Convert base64 to Blob
    const binaryString = atob(chunk.chunk);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: 'audio/wav' });

    audioQueueRef.current.push(blob);

    // Start playing if not already
    if (!isPlayingRef.current) {
      playNextChunk();
    }
  }, [playNextChunk]);

  // Track scroll position for jump-to-bottom button
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const isScrolledUp = target.scrollHeight - target.scrollTop - target.clientHeight > 100;
    setShowJumpToBottom(isScrolledUp);
  }, [setShowJumpToBottom]);

  // Scroll to bottom handler
  const scrollToBottom = useCallback(() => {
    messagesContainerRef.current?.scrollTo({
      top: messagesContainerRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, []);

  // Send message with pipelined LLM→TTS
  const sendPipelined = useCallback((text: string) => {
    if (!sessionId || !text.trim()) return;
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    sendMessagePipelined(
      sessionId,
      text.trim(),
      handleAudioChunk,
      () => {
        // onAudioDone — queue will finish naturally
        if (!isPlayingRef.current && audioQueueRef.current.length === 0) {
          setIsAudioPlaying(false);
        }
      },
    );
  }, [sessionId, sendMessagePipelined, handleAudioChunk]);

  // Handle text input send
  const handleTextSend = useCallback((text: string) => {
    sendPipelined(text);
  }, [sendPipelined]);

  // Handle followup question click
  const handleFollowupClick = useCallback((question: string) => {
    sendPipelined(question);
  }, [sendPipelined]);

  // Handle animal selection
  const handleAnimalSelect = useCallback((animal: string) => {
    sendPipelined(`Tell me about the ${animal}`);
  }, [sendPipelined]);

  // Handle rating
  const handleRate = useCallback((messageId: string, rating: 'up' | 'down') => {
    setRating(messageId, rating);
  }, [setRating]);

  // Handle "Want to see a picture?" button click
  const handleRequestImage = useCallback((messageId: string) => {
    if (!sessionId) return;
    const message = messages.find((m) => m.message_id === messageId);
    if (!message?.sources) return;

    const imageUrls = message.sources.flatMap((s) => s.image_urls || []);
    if (imageUrls.length > 0) {
      const animalName = message.sources[0]?.animal || 'this animal';
      addImageMessage(sessionId, imageUrls, animalName);
    }
  }, [sessionId, messages, addImageMessage]);

  // Handle voice overlay stop — flush recording, transcribe, then send through pipelined TTS.
  // Used by the overlay's Stop button AND by the 20s auto-stop timer.
  const handleVoiceStop = useCallback(async () => {
    if (!sessionId) return;
    const store = useVoiceStore.getState();
    if (store.mode !== 'recording') return; // already stopped or never started
    try {
      const blob = await store.stopRecording();
      if (!blob) return;
      const text = await store.transcribe(sessionId, blob);
      if (text && text.trim()) {
        sendPipelined(text.trim());
      }
    } catch (err) {
      console.error('Voice stop/transcribe failed:', err);
      useVoiceStore.getState().reset();
    }
  }, [sessionId, sendPipelined]);

  // Handle voice overlay cancel
  const handleVoiceCancel = useCallback(() => {
    // Voice store will handle the state reset
    useVoiceStore.getState().reset();
  }, []);

  // Safety net: auto-stop and submit any recording that runs longer than 20s
  // (kids' answers are short; this prevents stuck recordings on mobile).
  useEffect(() => {
    if (voiceMode !== 'recording') return;
    const MAX_RECORDING_MS = 20_000;
    const timer = setTimeout(() => {
      handleVoiceStop();
    }, MAX_RECORDING_MS);
    return () => clearTimeout(timer);
  }, [voiceMode, handleVoiceStop]);

  // Handle feedback submit
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

  // Interaction disabled state
  const isDisabled = sessionLoading || isStreaming || !sessionId || isAudioPlaying;
  const showVoiceOverlay = voiceMode === 'recording' || voiceMode === 'processing';
  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <>
      <ChatContainer
        header={<ChatHeader />}
        footer={
          <div className="flex flex-col">
            {/* Follow-up questions */}
            {followupQuestions.length > 0 && !isStreaming && !isAudioPlaying && (
              <div className="px-4 pt-2">
                <FollowupChips
                  questions={followupQuestions}
                  onSelect={handleFollowupClick}
                />
              </div>
            )}

            {/* Audio Player */}
            {audioBlob && (
              <div className="px-4 py-2">
                <Suspense fallback={<div className="text-center text-text-muted text-sm">Loading audio...</div>}>
                  <AudioPlayer audioBlob={audioBlob} autoPlay={true} onEnded={playNextChunk} />
                </Suspense>
              </div>
            )}

            {/* Input bar */}
            <InputBar
              onSend={handleTextSend}
              disabled={isDisabled}
            />
          </div>
        }
      >
        {/* Main scrollable content */}
        <div
          ref={messagesContainerRef}
          onScroll={handleScroll}
          className="min-h-full"
          role="log"
          aria-live="polite"
          aria-label="Chat messages"
        >
          {/* Welcome state */}
          {!hasMessages && (
            <>
              <WelcomeMessage />
              <AnimalGrid
                onSelectAnimal={handleAnimalSelect}
                disabled={isDisabled}
              />
            </>
          )}

          {/* Message list */}
          {hasMessages && (
            <MessageList
              messages={messages}
              isStreaming={isStreaming}
              streamingContent={streamingContent}
              sources={sources}
              onRate={handleRate}
              getRating={getRating}
              onRequestImage={handleRequestImage}
              onFeedback={() => setShowFeedbackModal(true)}
            />
          )}

          {/* Error display */}
          {error && (
            <div className="flex justify-center mt-4" role="alert" aria-live="assertive">
              <div className="px-4 py-3 bg-accent-error/10 border border-accent-error/30 text-accent-error rounded-bubble max-w-sm">
                <p className="font-medium text-sm">Something went wrong</p>
                <p className="text-xs mt-1">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Scroll to bottom FAB */}
        {showJumpToBottom && (
          <ScrollToBottom onClick={scrollToBottom} />
        )}
      </ChatContainer>

      {/* Voice overlay */}
      {showVoiceOverlay && (
        <VoiceOverlay onStop={handleVoiceStop} onCancel={handleVoiceCancel} />
      )}

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowFeedbackModal(false)}
        >
          <div
            className="bg-chat-elevated rounded-2xl p-6 max-w-md w-full shadow-2xl animate-message-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-heading font-bold text-text-primary">Share Your Feedback</h2>
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-chat-surface text-text-muted hover:text-text-primary transition-colors"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            {feedbackSubmitted ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-2">✅</div>
                <p className="text-text-primary font-medium">Thank you for your feedback!</p>
              </div>
            ) : (
              <>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Tell us what you think..."
                  maxLength={2000}
                  className="w-full h-32 px-4 py-3 bg-chat-surface border border-black/10 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-accent-primary/30 text-text-primary placeholder:text-text-muted font-body"
                />
                <div className="flex justify-between items-center mt-4">
                  <span className="text-sm text-text-muted">
                    {feedbackText.length} / 2000
                  </span>
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={!feedbackText.trim()}
                    className={`px-6 py-2 rounded-full font-medium transition-all ${
                      feedbackText.trim()
                        ? 'bg-accent-primary text-white hover:bg-accent-primary-hover active:scale-95'
                        : 'bg-chat-surface text-text-muted cursor-not-allowed'
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

      {/* Screen reader announcements */}
      <div className="sr-only" aria-live="assertive">
        {voiceMode === 'recording' && 'Recording started'}
        {voiceMode === 'processing' && 'Processing your message'}
      </div>
    </>
  );
}
