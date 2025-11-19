import { useState, useEffect } from 'react'
import ScenarioDashboard from './components/ScenarioDashboard'
import HumanActorInterface from './components/HumanActorInterface'
import { ScenarioStatus, WebSocketMessage } from './types'
import { apiClient } from './api/client'

/**
 * Main App component - Updated for V2 API
 *
 * Changes from V1.5:
 * - Uses V2 API client for all backend communication
 * - Manages scenario_id explicitly
 * - WebSocket connection via API client
 * - Maps V2 status to UI model
 */
function App() {
  const [status, setStatus] = useState<ScenarioStatus | null>(null)
  const [wsMessage, setWsMessage] = useState<WebSocketMessage | null>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch initial status
  useEffect(() => {
    initializeApp()
  }, [])

  // WebSocket connection - reconnect when scenario_id changes
  useEffect(() => {
    if (!status?.scenario_id) {
      return
    }

    let websocket: WebSocket | null = null

    // Connect to scenario's WebSocket stream
    try {
      websocket = apiClient.connectWebSocket(status.scenario_id, (event) => {
        console.log('V2 Event:', event)
        setWsMessage(event)

        // Update status based on event data
        if (event.type === 'turn_completed' && event.data.state) {
          updateStatusFromState(event.data.state)
        }
      })

      websocket.onerror = (event) => {
        console.error('WebSocket error:', event)
      }

      websocket.onclose = () => {
        console.log('WebSocket disconnected')
      }

      setWs(websocket)
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
    }

    // Cleanup: close WebSocket when component unmounts or scenario_id changes
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [status?.scenario_id])

  const initializeApp = async () => {
    try {
      // Check if there's an active scenario
      const scenarioId = apiClient.getActiveScenarioId()

      if (scenarioId) {
        // Fetch status of active scenario
        await fetchStatus(scenarioId)
      } else {
        // No active scenario - show empty state
        setLoading(false)
      }
    } catch (err) {
      console.error('Initialization error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }

  const fetchStatus = async (scenarioId?: string) => {
    try {
      const id = scenarioId || apiClient.getActiveScenarioId()
      if (!id) {
        setStatus(null)
        setLoading(false)
        return
      }

      const v2Status = await apiClient.getScenarioStatus(id)

      // Map V2 status to UI model
      const uiStatus: ScenarioStatus = {
        scenario_active: v2Status.status === 'running',
        scenario_path: null, // Not provided by V2 status
        current_turn: v2Status.current_turn,
        is_paused: false, // TODO: Add pause state to V2 API
        waiting_for_actor: v2Status.waiting_for_human || null,
        total_cost: v2Status.total_cost,
        actors: [], // TODO: Add actor tracking to V2 API
        scenario_id: v2Status.scenario_id,
        status: v2Status.status,
      }

      setStatus(uiStatus)
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch status:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }

  const updateStatusFromState = (state: any) => {
    if (!status) return

    setStatus({
      ...status,
      current_turn: state.turn || status.current_turn,
      total_cost: state.costs?.reduce((sum: number, cost: any) => sum + cost.cost, 0) || status.total_cost,
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="max-w-md">
          <div className="text-xl text-red-600 mb-4">Error: {error}</div>
          <button
            onClick={() => {
              setError(null)
              setLoading(true)
              initializeApp()
            }}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!status || !status.scenario_active) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="max-w-md text-center">
          <div className="text-xl text-gray-600 mb-4">No scenario running</div>
          <p className="text-sm text-gray-500 mb-6">
            Start a scenario using the V2 CLI or API to see it here.
          </p>
          <button
            onClick={() => {
              setLoading(true)
              initializeApp()
            }}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Check Again
          </button>
        </div>
      </div>
    )
  }

  // Check if this is a human actor's turn
  const isHumanTurn = status.waiting_for_actor !== null

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">
              Scenario Lab - V2
            </h1>
            <div className="text-sm text-gray-500">
              Scenario ID: {status.scenario_id}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Scenario Dashboard */}
          <ScenarioDashboard status={status} wsMessage={wsMessage} />

          {/* Human Actor Interface - Only show when it's a human's turn */}
          {isHumanTurn && status.waiting_for_actor && (
            <div className="mt-6">
              <HumanActorInterface
                actorName={status.waiting_for_actor}
                currentTurn={status.current_turn}
                onDecisionSubmitted={() => fetchStatus()}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
