/**
 * WebSocket TTS Hook
 * Provides real-time text-to-speech streaming via WebSocket
 * Features:
 * - Low-latency audio playback using Web Audio API
 * - PCM 24kHz float32 audio format
 * - Automatic reconnection handling
 * - Audio chunk queueing for seamless playback
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface TTSWebSocketMessage {
  type: 'text' | 'audio' | 'done' | 'error';
  data?: string; // base64 audio or error message
  sentence?: string; // for type='text'
  index?: number; // sentence index
}

interface UseTTSWebSocketOptions {
  sessionId: string;
  voice?: string;
  autoConnect?: boolean;
  onError?: (error: Error) => void;
}

/**
 * Hook for WebSocket-based TTS streaming
 * Connects to /voice/tts/ws endpoint and plays PCM audio chunks
 */
export function useTTSWebSocket({
  sessionId,
  voice = 'bella',
  autoConnect = true,
  onError,
}: UseTTSWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);

  /**
   * Get WebSocket URL (ws:// or wss://)
   */
  const getWebSocketUrl = useCallback((): string => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const apiUrl = import.meta.env.VITE_API_URL;

    if (apiUrl) {
      // Remove http/https and use ws/wss
      const host = apiUrl.replace(/^https?:\/\//, '');
      return `${protocol}//${host}/api/voice/tts/ws`;
    }

    // Default to same host
    return `${protocol}//${window.location.host}/api/voice/tts/ws`;
  }, []);

  /**
   * Initialize Web Audio API context
   */
  const initAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: 24000 });
    }
    return audioContextRef.current;
  }, []);

  /**
   * Convert base64 PCM to AudioBuffer
   */
  const base64ToAudioBuffer = useCallback(async (base64: string): Promise<AudioBuffer> => {
    const audioContext = initAudioContext();

    // Decode base64 to binary
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // Convert to Float32Array (PCM format)
    const float32Array = new Float32Array(bytes.buffer);

    // Create AudioBuffer
    const audioBuffer = audioContext.createBuffer(1, float32Array.length, 24000);
    audioBuffer.copyToChannel(float32Array, 0);

    return audioBuffer;
  }, [initAudioContext]);

  /**
   * Play next audio buffer in queue
   */
  const playNextInQueue = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsSpeaking(false);
      return;
    }

    const audioContext = initAudioContext();
    const audioBuffer = audioQueueRef.current.shift()!;

    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    currentSourceRef.current = source;
    isPlayingRef.current = true;
    setIsSpeaking(true);

    source.onended = () => {
      currentSourceRef.current = null;
      playNextInQueue();
    };

    source.start(0);
  }, [initAudioContext]);

  /**
   * Handle incoming WebSocket message
   */
  const handleMessage = useCallback(async (event: MessageEvent) => {
    try {
      const message: TTSWebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'audio':
          if (message.data) {
            // Convert base64 PCM to AudioBuffer and add to queue
            const audioBuffer = await base64ToAudioBuffer(message.data);
            audioQueueRef.current.push(audioBuffer);

            // Start playing if not already playing
            if (!isPlayingRef.current) {
              playNextInQueue();
            }
          }
          break;

        case 'done':
          // All audio chunks received
          break;

        case 'error':
          const errorMsg = message.data || 'WebSocket TTS error';
          setError(errorMsg);
          if (onError) {
            onError(new Error(errorMsg));
          }
          break;
      }
    } catch (err) {
      console.error('Failed to handle WebSocket message:', err);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMsg));
      }
    }
  }, [base64ToAudioBuffer, playNextInQueue, onError]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket TTS connected');
        setIsConnected(true);
        setError(null);

        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket TTS disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect after 3 seconds
        if (autoConnect) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      const errorMsg = err instanceof Error ? err.message : 'Connection failed';
      setError(errorMsg);
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMsg));
      }
    }
  }, [getWebSocketUrl, handleMessage, autoConnect, onError]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Send text to synthesize
   */
  const speak = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      const error = new Error('WebSocket not connected');
      setError('WebSocket not connected');
      if (onError) {
        onError(error);
      }
      return;
    }

    // Send message to WebSocket
    const message = {
      session_id: sessionId,
      text,
      voice,
    };

    wsRef.current.send(JSON.stringify(message));
    setError(null);
  }, [sessionId, voice, onError]);

  /**
   * Stop current playback
   */
  const stop = useCallback(() => {
    // Stop current audio source
    if (currentSourceRef.current) {
      currentSourceRef.current.stop();
      currentSourceRef.current = null;
    }

    // Clear audio queue
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setIsSpeaking(false);
  }, []);

  /**
   * Auto-connect on mount if enabled
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();

      // Clean up audio context
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    isSpeaking,
    error,
    speak,
    stop,
    connect,
    disconnect,
  };
}
