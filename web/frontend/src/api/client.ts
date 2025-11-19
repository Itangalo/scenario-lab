/**
 * API Client for Scenario Lab V2
 *
 * Provides a clean interface to the V2 REST API while maintaining
 * a simple "active scenario" model for the UI.
 */

export interface V2ScenarioStatus {
  scenario_id: string
  status: string  // 'running', 'completed', 'halted', 'failed'
  current_turn: number
  total_cost: number
  started_at: string
  completed_at?: string
  error?: string
}

export interface V2RunSummary {
  run_id: string
  scenario_name: string
  status: string
  turns: number
  total_cost: number
  created: string
}

export interface V2ScenarioExecuteRequest {
  scenario_path: string
  max_turns?: number
  credit_limit?: number
  output_path?: string
  enable_database?: boolean
}

export interface V2Event {
  type: string
  data: Record<string, any>
  timestamp: string
  source?: string
}

/**
 * API Client for V2 endpoints
 */
class ScenarioLabAPI {
  private baseUrl: string
  private activeScenarioId: string | null = null

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl
  }

  /**
   * Start a new scenario execution
   */
  async executeScenario(request: V2ScenarioExecuteRequest): Promise<V2ScenarioStatus> {
    const response = await fetch(`${this.baseUrl}/api/scenarios/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to execute scenario')
    }

    const status = await response.json()
    this.activeScenarioId = status.scenario_id
    return status
  }

  /**
   * Get status of a running scenario
   */
  async getScenarioStatus(scenarioId?: string): Promise<V2ScenarioStatus> {
    const id = scenarioId || this.activeScenarioId
    if (!id) {
      throw new Error('No active scenario')
    }

    const response = await fetch(`${this.baseUrl}/api/scenarios/${id}/status`)

    if (!response.ok) {
      throw new Error('Failed to fetch scenario status')
    }

    return await response.json()
  }

  /**
   * Get the active scenario ID
   */
  getActiveScenarioId(): string | null {
    return this.activeScenarioId
  }

  /**
   * Set the active scenario ID
   */
  setActiveScenarioId(id: string | null): void {
    this.activeScenarioId = id
  }

  /**
   * List all runs
   */
  async listRuns(scenario?: string): Promise<V2RunSummary[]> {
    const url = scenario
      ? `${this.baseUrl}/api/runs?scenario=${encodeURIComponent(scenario)}`
      : `${this.baseUrl}/api/runs`

    const response = await fetch(url)

    if (!response.ok) {
      throw new Error('Failed to list runs')
    }

    return await response.json()
  }

  /**
   * Get detailed run information
   */
  async getRun(runId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/runs/${runId}`)

    if (!response.ok) {
      throw new Error('Failed to fetch run details')
    }

    return await response.json()
  }

  /**
   * Get run statistics
   */
  async getRunStatistics(runId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/runs/${runId}/statistics`)

    if (!response.ok) {
      throw new Error('Failed to fetch run statistics')
    }

    return await response.json()
  }

  /**
   * Compare multiple runs
   */
  async compareRuns(runIds: string[]): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/runs/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(runIds),
    })

    if (!response.ok) {
      throw new Error('Failed to compare runs')
    }

    return await response.json()
  }

  /**
   * Aggregate metrics across runs
   */
  async aggregateMetric(metricName: string, scenario?: string): Promise<any> {
    const url = scenario
      ? `${this.baseUrl}/api/metrics/${metricName}/aggregate?scenario=${encodeURIComponent(scenario)}`
      : `${this.baseUrl}/api/metrics/${metricName}/aggregate`

    const response = await fetch(url)

    if (!response.ok) {
      throw new Error('Failed to aggregate metric')
    }

    return await response.json()
  }

  /**
   * Pause a running scenario
   */
  async pauseScenario(scenarioId?: string): Promise<void> {
    const id = scenarioId || this.activeScenarioId
    if (!id) {
      throw new Error('No active scenario to pause')
    }

    const response = await fetch(`${this.baseUrl}/api/scenarios/${id}/pause`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Failed to pause scenario')
    }
  }

  /**
   * Resume a paused scenario
   */
  async resumeScenario(scenarioId?: string): Promise<void> {
    const id = scenarioId || this.activeScenarioId
    if (!id) {
      throw new Error('No active scenario to resume')
    }

    const response = await fetch(`${this.baseUrl}/api/scenarios/${id}/resume`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Failed to resume scenario')
    }
  }

  /**
   * Submit human actor decision
   */
  async submitHumanDecision(
    actor: string,
    decision: {
      long_term_goals: string[]
      short_term_priorities: string[]
      reasoning: string
      action: string
    },
    scenarioId?: string
  ): Promise<void> {
    const id = scenarioId || this.activeScenarioId
    if (!id) {
      throw new Error('No active scenario for decision submission')
    }

    const response = await fetch(`${this.baseUrl}/api/scenarios/${id}/human-decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        actor,
        ...decision,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to submit decision')
    }
  }

  /**
   * Create WebSocket connection for real-time scenario updates
   */
  connectWebSocket(scenarioId?: string, onEvent?: (event: V2Event) => void): WebSocket {
    const id = scenarioId || this.activeScenarioId
    if (!id) {
      throw new Error('No active scenario for WebSocket connection')
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = this.baseUrl ? new URL(this.baseUrl).host : window.location.host
    const ws = new WebSocket(`${protocol}//${host}/api/scenarios/${id}/stream`)

    if (onEvent) {
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        onEvent(data)
      }
    }

    return ws
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${this.baseUrl}/api/health`)

    if (!response.ok) {
      throw new Error('Health check failed')
    }

    return await response.json()
  }
}

// Export singleton instance
export const apiClient = new ScenarioLabAPI()
