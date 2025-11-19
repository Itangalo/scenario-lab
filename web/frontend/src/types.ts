// Type definitions for Scenario Lab API

/**
 * Scenario status (compatible with both V1.5 and V2)
 */
export interface ScenarioStatus {
  scenario_active: boolean
  scenario_path: string | null
  current_turn: number
  is_paused: boolean
  waiting_for_actor: string | null
  total_cost: number
  actors: ActorInfo[]
  scenario_id?: string  // V2 specific
  status?: string  // V2 specific: 'running', 'completed', 'halted', 'failed'
}

export interface ActorInfo {
  name: string
  control: 'ai' | 'human'
  status: 'waiting' | 'thinking' | 'complete' | 'your_turn'
}

export interface ScenarioInfo {
  name: string
  path: string
}

export interface HumanDecisionRequest {
  long_term_goals: string[]
  short_term_priorities: string[]
  reasoning: string
  action: string
}

/**
 * WebSocket message format (V2 events)
 */
export interface WebSocketMessage {
  type: string  // Event type from V2 API
  data: {
    turn?: number
    state?: any
    actor?: string
    phase?: string
    reason?: string
    error?: string
    [key: string]: any
  }
  timestamp: string
  source?: string
}

/**
 * Legacy WebSocket message format (for compatibility)
 */
export interface LegacyWebSocketMessage {
  type: 'turn_start' | 'turn_complete' | 'waiting_for_human' | 'human_decision_processed' |
        'actor_thinking' | 'actor_complete' | 'scenario_complete' | 'scenario_halted' |
        'scenario_stopped' | 'timeout' | 'error'
  current_turn: number
  is_running: boolean
  is_paused: boolean
  waiting_for_actor: string | null
  total_cost: number
  actor?: string
  turn?: number
  message?: string
  decision?: string
  reasoning?: string
  reason?: string
  error?: string
}
