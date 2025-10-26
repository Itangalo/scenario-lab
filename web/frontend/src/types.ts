// Type definitions for Scenario Lab API

export interface ScenarioStatus {
  scenario_active: boolean
  scenario_path: string | null
  current_turn: number
  is_paused: boolean
  waiting_for_actor: string | null
  total_cost: number
  actors: ActorInfo[]
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

export interface WebSocketMessage {
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
