import { ScenarioStatus, WebSocketMessage } from '../types'

interface Props {
  status: ScenarioStatus
  wsMessage: WebSocketMessage | null
}

export default function ScenarioDashboard({ status, wsMessage }: Props) {
  const getActorStatusColor = (actor: { status: string }) => {
    switch (actor.status) {
      case 'thinking':
        return 'bg-yellow-100 text-yellow-800'
      case 'complete':
        return 'bg-green-100 text-green-800'
      case 'your_turn':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Turn Progress */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Current Turn</h3>
              <p className="mt-1 text-3xl font-semibold text-indigo-600">
                {status.current_turn}
              </p>
            </div>
            <div className="text-right">
              <h3 className="text-lg font-medium text-gray-900">Total Cost</h3>
              <p className="mt-1 text-3xl font-semibold text-green-600">
                ${status.total_cost.toFixed(4)}
              </p>
            </div>
          </div>

          {status.is_paused && (
            <div className="mt-4 flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400 animate-pulse" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-yellow-800">
                  Scenario paused - waiting for human decision
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Actor Status Grid */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Actor Status</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {status.actors.map((actor, idx) => (
              <div
                key={idx}
                className={`relative rounded-lg border border-gray-300 px-4 py-3 ${
                  status.waiting_for_actor === actor.name ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {actor.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {actor.control === 'human' ? '👤 Human' : '🤖 AI'}
                    </p>
                  </div>
                  <div>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActorStatusColor(
                        actor
                      )}`}
                    >
                      {actor.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity Feed */}
      {wsMessage && (
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
            <div className="flow-root">
              <div className="-mb-8">
                <div className="relative pb-8">
                  <div className="relative flex space-x-3">
                    <div>
                      <span className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ring-8 ring-white">
                        <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                        </svg>
                      </span>
                    </div>
                    <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                      <div>
                        <p className="text-sm text-gray-500">
                          {wsMessage.message || getEventDescription(wsMessage)}
                        </p>
                        {wsMessage.actor && (
                          <p className="mt-1 text-sm text-gray-900">
                            Actor: <span className="font-medium">{wsMessage.actor}</span>
                          </p>
                        )}
                      </div>
                      <div className="whitespace-nowrap text-right text-sm text-gray-500">
                        <time>Just now</time>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function getEventDescription(message: WebSocketMessage): string {
  switch (message.type) {
    case 'turn_start':
      return `Turn ${message.turn} started`
    case 'turn_complete':
      return `Turn ${message.turn} completed`
    case 'waiting_for_human':
      return `Waiting for ${message.actor} to make a decision`
    case 'human_decision_processed':
      return `Decision from ${message.actor} processed`
    case 'actor_thinking':
      return `${message.actor} is thinking...`
    case 'actor_complete':
      return `${message.actor} completed their decision`
    case 'scenario_complete':
      return 'Scenario completed'
    case 'scenario_halted':
      return `Scenario halted: ${message.reason}`
    case 'scenario_stopped':
      return 'Scenario stopped by user'
    case 'timeout':
      return 'Decision timeout'
    case 'error':
      return `Error: ${message.error}`
    default:
      return 'Unknown event'
  }
}
