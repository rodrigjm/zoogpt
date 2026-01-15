// Analytics Types
export interface TodayMetrics {
  sessions: number
  questions: number
  avg_latency_ms: number | null
  error_rate: number
}

export interface DailyTrend {
  date: string
  sessions: number
  questions: number
  avg_latency_ms: number | null
}

export interface TopQuestion {
  question: string
  count: number
}

export interface TopAnimal {
  name: string
  count: number
}

export interface DashboardData {
  today: TodayMetrics
  trends: DailyTrend[]
  top_questions: TopQuestion[]
  top_animals: TopAnimal[]
}

export interface SessionSummary {
  session_id: string
  start_time: string
  duration_seconds: number | null
  message_count: number
  avg_latency_ms: number | null
  client_type: string | null
}

export interface InteractionDetail {
  id: number
  timestamp: string
  question: string
  answer: string
  sources: Array<{ animal: string; title: string }> | null
  confidence_score: number | null
  latency_ms: number
  rag_latency_ms: number | null
  llm_latency_ms: number | null
  tts_latency_ms: number | null
}

export interface PercentileStats {
  p50: number | null
  p90: number | null
  p99: number | null
  avg: number | null
  count: number
}

export interface LatencyBreakdown {
  overall: PercentileStats
  rag: PercentileStats
  llm: PercentileStats
  tts: PercentileStats
}

// Knowledge Base Types
export interface Animal {
  id: number
  name: string
  display_name: string
  category: string | null
  source_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Source {
  id: number
  title: string
  url: string | null
  chunk_count: number
  last_indexed: string | null
  created_at: string
}

export interface AnimalDetail extends Animal {
  sources: Source[]
}

export interface IndexStatus {
  status: 'ready' | 'rebuilding' | 'failed'
  last_rebuild: string | null
  document_count: number
  chunk_count: number
  error_message: string | null
}

// Configuration Types
export interface PromptsConfig {
  system_prompt: string
  fallback_response: string
  followup_questions: string[]
}

export interface ModelConfig {
  name: string
  temperature: number
  max_tokens: number
}

export interface VoicePreset {
  id: string
  name: string
  description: string
}

export interface TTSConfig {
  provider: 'kokoro' | 'openai'
  default_voice: string
  speed: number
  fallback_provider: string
  available_voices: Record<string, VoicePreset[]>
}

export interface FullConfig {
  version: string
  prompts: PromptsConfig
  model: ModelConfig
  tts: TTSConfig
}

// Auth Types
export interface User {
  username: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_at: string
}
