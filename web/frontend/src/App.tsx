import { useState, useEffect } from 'react'
import ScenarioDashboard from './components/ScenarioDashboard'
import HumanActorInterface from './components/HumanActorInterface'
import { ScenarioStatus, WebSocketMessage } from './types'

function App() {
  const [status, setStatus] = useState<ScenarioStatus | null>(null)
  const [wsMessage, setWsMessage] = useState<WebSocketMessage | null>(null)
  const [, setWs] = useState<WebSocket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch initial status
  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 2000) // Poll every 2 seconds
    return () => clearInterval(interval)
  }, [])

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected')
    }

    websocket.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      console.log('WebSocket message:', message)
      setWsMessage(message)

      // Update status based on message
      if (status) {
        setStatus({
          ...status,
          current_turn: message.current_turn,
          is_paused: message.is_paused,
          waiting_for_actor: message.waiting_for_actor,
          total_cost: message.total_cost,
        })
      }
    }

    websocket.onerror = (event) => {
      console.error('WebSocket error:', event)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/status')
      if (!response.ok) throw new Error('Failed to fetch status')
      const data = await response.json()
      setStatus(data)
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
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
        <div className="text-xl text-red-600">Error: {error}</div>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">No scenario running</div>
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
          <h1 className="text-3xl font-bold text-gray-900">
            Scenario Lab - Human Interface
          </h1>
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
                onDecisionSubmitted={fetchStatus}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
