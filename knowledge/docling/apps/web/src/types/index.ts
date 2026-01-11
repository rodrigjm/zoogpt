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

// ===== Chat Types =====

export interface ChatRequest {
  session_id: string;
  message: string;
  mode: 'rag';
  metadata?: Record<string, unknown>;
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  reply: string;
  sources: unknown[]; // To be defined based on RAG implementation
  created_at: string; // ISO-8601
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

// ===== Health Types =====

export interface HealthResponse {
  ok: boolean;
}
