export interface Artifact {
  id: string;
  type: string;
  title: string;
  description?: string;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  message?: string;
  query?: string;
  conversation_id?: string;
  thread_id?: string;
  latitude?: number;
  longitude?: number;
}

export interface ChatResponse {
  conversation_id: string;
  thread_id: string;
  response: string;
  artifacts: Artifact[];
  route_path?: string;
  detected_language?: string;
  intent?: string;
  risk_level?: string;
  risk_score?: number;
  confidence_score?: number;
  gate_decision?: string;
  node_trace?: string[];
  errors?: string[];
  location?: Record<string, any>;
  active_context?: Record<string, any>;
}

export interface ConversationSummary {
  conversation_id: string;
  thread_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: Array<{
    role: string;
    content: string;
    timestamp?: string;
  }>;
  active_context?: Record<string, any>;
  context_summary?: string;
  artifacts: Artifact[];
}

export interface EvidenceRecord {
  source_id: string;
  provider: string;
  dataset: string;
  source_type: string;
  authority_class: string;
  data_class: string;
  status: string;
  retrieved_at: string;
  observation_time?: string;
  forecast_time?: string;
  valid_until?: string;
  freshness?: {
    age_minutes: number | null;
    freshness_status: string;
    ref_timestamp: string | null;
  };
  attribution?: string;
  license_type?: string;
  limitations?: string[];
}

export interface EvidenceSummary {
  total_sources: number;
  available_count: number;
  unavailable_count: number;
  stale_count: number;
  completeness_score: number;
  available_sources: string[];
  unavailable_sources: string[];
  stale_sources: string[];
  decision_support_only?: boolean;
}

export interface AgentStepPayload {
  id?: string;
  node: string;
  status: string;
  message: string;
  thought: string;
  icon: string;
  label: string;
  summary?: Record<string, any>;
  path?: string;
}
