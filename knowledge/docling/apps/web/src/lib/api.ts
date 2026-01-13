/**
 * API client for Zoocari backend
 * Uses native fetch with type-safe wrappers
 * All endpoints proxy through Vite to http://localhost:8000
 */

import type {
  CreateSessionRequest,
  CreateSessionResponse,
  GetSessionResponse,
  ChatRequest,
  ChatResponse,
  SttRequest,
  SttResponse,
  TtsRequest,
  TtsStreamRequest,
  TtsStreamAudioChunk,
  TtsStreamDoneData,
  HealthResponse,
  ApiError,
  StreamChunk,
} from '../types';

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = 'API request failed';
    try {
      const error: ApiError = await response.json();
      errorMessage = error.error.message || errorMessage;
    } catch {
      // If JSON parsing fails, use status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

// ===== Session API =====

export async function createSession(
  request: CreateSessionRequest
): Promise<CreateSessionResponse> {
  return apiFetch<CreateSessionResponse>('/session', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getSession(
  sessionId: string
): Promise<GetSessionResponse> {
  return apiFetch<GetSessionResponse>(`/session/${sessionId}`, {
    method: 'GET',
  });
}

// ===== Chat API =====

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Stream chat response via SSE
 * Calls onChunk for each text chunk and onComplete when done
 */
export async function streamChatMessage(
  request: ChatRequest,
  onChunk: (chunk: StreamChunk) => void,
  onComplete?: (data: { followup_questions?: string[]; sources?: any[] }) => void,
  onError?: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMessage = 'Stream request failed';
      try {
        const error: ApiError = await response.json();
        errorMessage = error.error.message || errorMessage;
      } catch {
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') {
            continue;
          }

          try {
            const chunk: StreamChunk = JSON.parse(data);
            onChunk(chunk);

            if (chunk.type === 'done' && onComplete) {
              onComplete({
                followup_questions: chunk.followup_questions,
                sources: chunk.sources,
              });
            } else if (chunk.type === 'error') {
              throw new Error(chunk.content || 'Stream error');
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE chunk:', parseError);
          }
        }
      }
    }
  } catch (error) {
    if (onError) {
      onError(error instanceof Error ? error : new Error('Unknown error'));
    } else {
      throw error;
    }
  }
}

// ===== Voice API =====

export async function speechToText(
  request: SttRequest
): Promise<SttResponse> {
  const formData = new FormData();
  formData.append('session_id', request.session_id);
  formData.append('audio', request.audio);

  const response = await fetch(`${API_BASE}/voice/stt`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type header - browser will set it with boundary
  });

  if (!response.ok) {
    let errorMessage = 'STT request failed';
    try {
      const error: ApiError = await response.json();
      errorMessage = error.error.message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function textToSpeech(
  request: TtsRequest
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/voice/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorMessage = 'TTS request failed';
    try {
      const error: ApiError = await response.json();
      errorMessage = error.error.message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  // Get the blob and ensure correct MIME type for audio playback
  const blob = await response.blob();
  // Re-create blob with explicit audio/wav type to ensure browser recognizes it
  return new Blob([blob], { type: 'audio/wav' });
}

/**
 * Stream TTS audio via SSE as RAG response is generated.
 * Reduces latency by sending audio sentence-by-sentence.
 *
 * @param request - Session ID, user message, and optional voice
 * @param onAudioChunk - Called for each audio chunk (base64 WAV)
 * @param onComplete - Called when streaming is complete
 * @param onError - Called on error
 */
export async function streamTextToSpeech(
  request: TtsStreamRequest,
  onAudioChunk: (chunk: TtsStreamAudioChunk) => void,
  onComplete?: (data: TtsStreamDoneData) => void,
  onError?: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/voice/tts/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMessage = 'TTS stream request failed';
      try {
        const error: ApiError = await response.json();
        errorMessage = error.error.message || errorMessage;
      } catch {
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        // Handle SSE event format
        if (line.startsWith('event: ')) {
          continue; // Event type is in the next data line
        }

        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') {
            continue;
          }

          try {
            const parsed = JSON.parse(data);

            // Check what type of event this is based on content
            if ('chunk' in parsed && 'sentence' in parsed) {
              // Audio chunk event
              onAudioChunk(parsed as TtsStreamAudioChunk);
            } else if ('total_sentences' in parsed) {
              // Done event
              if (onComplete) {
                onComplete(parsed as TtsStreamDoneData);
              }
            } else if ('code' in parsed && 'message' in parsed) {
              // Error event
              throw new Error(parsed.message || 'Stream error');
            }
          } catch (parseError) {
            if (parseError instanceof SyntaxError) {
              console.warn('Failed to parse SSE chunk:', parseError);
            } else {
              throw parseError;
            }
          }
        }
      }
    }
  } catch (error) {
    if (onError) {
      onError(error instanceof Error ? error : new Error('Unknown error'));
    } else {
      throw error;
    }
  }
}

// ===== Health API =====

export async function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health', {
    method: 'GET',
  });
}
