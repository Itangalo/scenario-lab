import { useState, useEffect } from 'react'
import { ScenarioStatus, WebSocketMessage, ActivityItem } from '../types'

interface Props {
  status: ScenarioStatus
  wsMessage: WebSocketMessage | null
}

// Max number of activity items to keep
const MAX_ACTIVITY_ITEMS = 50

export default function ScenarioDashboard({ status, wsMessage }: Props) {
  const [activityFeed, setActivityFeed] = useState<ActivityItem[]>([])
  const [activeActors, setActiveActors] = useState<Map<string, string>>(new Map())
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  // Process incoming WebSocket messages
  useEffect(() => {
    if (!wsMessage) return

    // Create activity item from WebSocket message
    const activityItem = createActivityItem(wsMessage)
    if (activityItem) {
      setActivityFeed(prev => {
        const updated = [activityItem, ...prev].slice(0, MAX_ACTIVITY_ITEMS)
        return updated
      })
    }

    // Update active actors based on event type
    updateActiveActors(wsMessage)
  }, [wsMessage])

  const updateActiveActors = (message: WebSocketMessage) => {
    const { type, data } = message

    if (type === 'actor_decision_started' && data.actor) {
      setActiveActors(prev => {
        const updated = new Map(prev)
        updated.set(data.actor!, 'thinking')
        return updated
      })
    } else if (type === 'actor_decision_completed' && data.actor) {
      setActiveActors(prev => {
        const updated = new Map(prev)
        updated.set(data.actor!, 'complete')
        return updated
      })
    } else if (type === 'turn_started') {
      // Clear all actor statuses at start of turn
      setActiveActors(new Map())
    }
  }

  const toggleExpanded = (id: string) => {
    setExpandedItems(prev => {
      const updated = new Set(prev)
      if (updated.has(id)) {
        updated.delete(id)
      } else {
        updated.add(id)
      }
      return updated
    })
  }

  const getActorStatusColor = (actorStatus: string) => {
    switch (actorStatus) {
      case 'thinking':
        return 'bg-yellow-100 text-yellow-800 animate-pulse'
      case 'complete':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'actor_decision_started':
        return '🤔'
      case 'actor_decision_completed':
        return '✅'
      case 'world_state_updated':
        return '🌍'
      case 'communication_sent':
        return '💬'
      case 'turn_started':
        return '▶️'
      case 'turn_completed':
        return '✔️'
      case 'phase_started':
        return '⚙️'
      case 'phase_completed':
        return '✓'
      default:
        return '📌'
    }
  }

  // Get all unique actors from config and active states
  const allActors = Array.from(new Set([
    ...status.actors.map(a => a.name),
    ...Array.from(activeActors.keys())
  ]))

  return (
    <div className="space-y-6">
      {/* Turn Progress and Cost */}
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

      {/* Active Actors Grid */}
      {allActors.length > 0 && (
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Actor Status</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {allActors.map((actorName, idx) => {
                const actorStatus = activeActors.get(actorName) || 'idle'
                const configActor = status.actors.find(a => a.name === actorName)

                return (
                  <div
                    key={idx}
                    className={`relative rounded-lg border border-gray-300 px-4 py-3 ${
                      actorStatus === 'thinking' ? 'ring-2 ring-yellow-500' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {actorName}
                        </p>
                        <p className="text-sm text-gray-500">
                          {configActor?.control === 'human' ? '👤 Human' : '🤖 AI'}
                        </p>
                      </div>
                      <div>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActorStatusColor(actorStatus)}`}
                        >
                          {actorStatus === 'thinking' ? 'Thinking...' : actorStatus}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Real-Time Activity Feed */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Live Activity Feed
            {activityFeed.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                ({activityFeed.length} events)
              </span>
            )}
          </h3>

          {activityFeed.length === 0 ? (
            <p className="text-gray-500 text-sm">Waiting for events...</p>
          ) : (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {activityFeed.map((item) => (
                <ActivityItemCard
                  key={item.id}
                  item={item}
                  isExpanded={expandedItems.has(item.id)}
                  onToggle={() => toggleExpanded(item.id)}
                  getEventIcon={getEventIcon}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface ActivityItemCardProps {
  item: ActivityItem
  isExpanded: boolean
  onToggle: () => void
  getEventIcon: (type: string) => string
}

function ActivityItemCard({ item, isExpanded, onToggle, getEventIcon }: ActivityItemCardProps) {
  const hasContent = item.action || item.reasoning || item.world_state || item.content

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
      <div
        className={`flex items-start space-x-3 ${hasContent ? 'cursor-pointer' : ''}`}
        onClick={hasContent ? onToggle : undefined}
      >
        <span className="text-xl">{getEventIcon(item.type)}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-900">
              {getActivityTitle(item)}
            </p>
            <div className="flex items-center space-x-2">
              {item.turn !== undefined && (
                <span className="text-xs text-gray-500">Turn {item.turn}</span>
              )}
              <time className="text-xs text-gray-500">
                {formatTimestamp(item.timestamp)}
              </time>
              {hasContent && (
                <svg
                  className={`h-4 w-4 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </div>
          </div>

          {/* Preview when collapsed */}
          {!isExpanded && hasContent && (
            <p className="mt-1 text-sm text-gray-500 truncate">
              {getPreviewText(item)}
            </p>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && hasContent && (
        <div className="mt-4 ml-9 space-y-3">
          {/* Actor Decision Content */}
          {item.goals && item.goals.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Goals</h4>
              <ul className="mt-1 text-sm text-gray-600 list-disc list-inside">
                {item.goals.map((goal, idx) => (
                  <li key={idx}>{goal}</li>
                ))}
              </ul>
            </div>
          )}

          {item.reasoning && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Reasoning</h4>
              <div className="mt-1 text-sm text-gray-600 whitespace-pre-wrap max-h-48 overflow-y-auto bg-gray-50 p-3 rounded">
                {item.reasoning}
              </div>
            </div>
          )}

          {item.action && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Action</h4>
              <div className="mt-1 text-sm text-gray-600 whitespace-pre-wrap max-h-48 overflow-y-auto bg-blue-50 p-3 rounded border-l-4 border-blue-400">
                {item.action}
              </div>
            </div>
          )}

          {/* World State Content */}
          {item.world_state && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">World State</h4>
              <div className="mt-1 text-sm text-gray-600 whitespace-pre-wrap max-h-64 overflow-y-auto bg-green-50 p-3 rounded border-l-4 border-green-400">
                {item.world_state}
              </div>
            </div>
          )}

          {item.key_changes && item.key_changes.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Key Changes</h4>
              <ul className="mt-1 text-sm text-gray-600 list-disc list-inside">
                {item.key_changes.map((change, idx) => (
                  <li key={idx}>{change}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Communication Content */}
          {item.content && item.type === 'communication_sent' && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                Message from {item.sender} to {item.recipients?.join(', ') || 'all'}
              </h4>
              <div className="mt-1 text-sm text-gray-600 whitespace-pre-wrap max-h-48 overflow-y-auto bg-purple-50 p-3 rounded border-l-4 border-purple-400">
                {item.content}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function createActivityItem(message: WebSocketMessage): ActivityItem | null {
  const { type, data, timestamp } = message

  // Only create items for relevant event types
  const relevantTypes = [
    'actor_decision_started',
    'actor_decision_completed',
    'world_state_updated',
    'communication_sent',
    'turn_started',
    'turn_completed',
    'phase_started',
    'phase_completed',
    'scenario_completed',
    'scenario_halted',
    'scenario_failed',
  ]

  if (!relevantTypes.includes(type)) {
    return null
  }

  return {
    id: `${type}-${timestamp}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    timestamp,
    actor: data.actor,
    content: data.content,
    goals: data.goals,
    reasoning: data.reasoning,
    action: data.action,
    world_state: data.world_state,
    key_changes: data.key_changes,
    sender: data.sender,
    recipients: data.recipients,
    turn: data.turn,
  }
}

function getActivityTitle(item: ActivityItem): string {
  switch (item.type) {
    case 'actor_decision_started':
      return `${item.actor} is thinking...`
    case 'actor_decision_completed':
      return `${item.actor} made a decision`
    case 'world_state_updated':
      return 'World state updated'
    case 'communication_sent':
      return `${item.sender} sent a message`
    case 'turn_started':
      return `Turn ${item.turn} started`
    case 'turn_completed':
      return `Turn ${item.turn} completed`
    case 'phase_started':
      return `Phase started`
    case 'phase_completed':
      return `Phase completed`
    case 'scenario_completed':
      return 'Scenario completed'
    case 'scenario_halted':
      return 'Scenario halted'
    case 'scenario_failed':
      return 'Scenario failed'
    default:
      return `Event: ${item.type}`
  }
}

function getPreviewText(item: ActivityItem): string {
  if (item.action) {
    return item.action.substring(0, 150) + (item.action.length > 150 ? '...' : '')
  }
  if (item.world_state) {
    return item.world_state.substring(0, 150) + (item.world_state.length > 150 ? '...' : '')
  }
  if (item.content) {
    return item.content.substring(0, 150) + (item.content.length > 150 ? '...' : '')
  }
  if (item.reasoning) {
    return item.reasoning.substring(0, 150) + (item.reasoning.length > 150 ? '...' : '')
  }
  return ''
}

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  } catch {
    return timestamp
  }
}
