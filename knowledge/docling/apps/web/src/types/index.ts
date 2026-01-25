/**
 * TypeScript types matching CONTRACT.md Part 4
 * These interfaces align with the FastAPI backend API shapes.
 */

// ===== Common Types =====

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// ===== Session Types =====

export interface CreateSessionRequest {
  client: string;
  metadata?: Record<string, unknown>;
}

export interface CreateSessionResponse {
  session_id: string;
  created_at: string; // ISO-8601
}

export interface GetSessionResponse {
  session_id: string;
  created_at: string; // ISO-8601
  metadata?: Record<string, unknown>;
}

export interface Session {
  session_id: string;
  created_at: string; // ISO-8601
  last_active?: string; // ISO-8601
  message_count: number;
  client: string;
  metadata?: Record<string, unknown>;
}

export interface ChatMessage {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string; // ISO-8601
  metadata?: Record<string, unknown>;
}

// ===== Chat Types =====

export interface ChatRequest {
  session_id: string;
  message: string;
  mode: 'rag';
  metadata?: Record<string, unknown>;
}

export interface Source {
  animal: string;
  title: string;
  url?: string;
  thumbnail?: string;
  image_urls?: string[];
  alt?: string;
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  reply: string;
  sources: Source[];
  created_at: string; // ISO-8601
  followup_questions: string[];
  confidence: number; // 0.0 - 1.0
}

export interface StreamChunk {
  type: 'text' | 'done' | 'error';
  content?: string;
  followup_questions?: string[];
  sources?: Source[];
}

// ===== Voice Types (STT/TTS) =====

export interface SttRequest {
  session_id: string;
  audio: File; // multipart/form-data
}

export interface SttResponse {
  session_id: string;
  text: string;
}

export interface TtsRequest {
  session_id: string;
  text: string;
  voice?: string;
}

// TTS response is audio bytes (audio/mpeg or audio/wav)
// No JSON response type needed

// Streaming TTS (generates audio from query via RAG + TTS pipeline)
export interface TtsStreamRequest {
  session_id: string;
  message: string; // User query to generate response for
  voice?: string;
}

export interface TtsStreamAudioChunk {
  chunk: string; // base64 encoded WAV audio
  sentence: string; // The sentence that was synthesized
  index: number; // Sentence index for ordering
}

export interface TtsStreamDoneData {
  total_sentences: number;
  sources?: Source[];
}

// WebSocket TTS Types
export interface TTSWebSocketMessage {
  type: 'text' | 'audio' | 'done' | 'error';
  data?: string; // base64 audio or error message
  sentence?: string; // for type='text'
  index?: number; // sentence index
}

export interface TTSWebSocketRequest {
  session_id: string;
  text: string;
  voice?: string;
}

// ===== Health Types =====

export interface HealthResponse {
  ok: boolean;
}

// ===== Feedback Types =====

export interface RatingRequest {
  session_id: string;
  message_id: string;
  rating: 'up' | 'down';
}

export interface SurveyRequest {
  session_id: string;
  comment: string;
}

export interface FeedbackResponse {
  id: number;
  created_at: string; // ISO-8601
  success: boolean;
}
