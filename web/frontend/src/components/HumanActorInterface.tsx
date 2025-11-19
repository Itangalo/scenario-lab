import { useState } from 'react'
import { HumanDecisionRequest } from '../types'
import { apiClient } from '../api/client'

interface Props {
  actorName: string
  currentTurn: number
  onDecisionSubmitted: () => void
}

export default function HumanActorInterface({ actorName, currentTurn, onDecisionSubmitted }: Props) {
  const [goals, setGoals] = useState<string[]>([''])
  const [priorities, setPriorities] = useState<string[]>([''])
  const [reasoning, setReasoning] = useState('')
  const [action, setAction] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addGoal = () => {
    setGoals([...goals, ''])
  }

  const removeGoal = (index: number) => {
    setGoals(goals.filter((_, i) => i !== index))
  }

  const updateGoal = (index: number, value: string) => {
    const newGoals = [...goals]
    newGoals[index] = value
    setGoals(newGoals)
  }

  const addPriority = () => {
    setPriorities([...priorities, ''])
  }

  const removePriority = (index: number) => {
    setPriorities(priorities.filter((_, i) => i !== index))
  }

  const updatePriority = (index: number, value: string) => {
    const newPriorities = [...priorities]
    newPriorities[index] = value
    setPriorities(newPriorities)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    // Filter out empty goals and priorities
    const filteredGoals = goals.filter(g => g.trim() !== '')
    const filteredPriorities = priorities.filter(p => p.trim() !== '')

    if (filteredGoals.length === 0) {
      setError('Please add at least one long-term goal')
      setSubmitting(false)
      return
    }

    if (filteredPriorities.length === 0) {
      setError('Please add at least one short-term priority')
      setSubmitting(false)
      return
    }

    if (!reasoning.trim()) {
      setError('Please provide reasoning for your decision')
      setSubmitting(false)
      return
    }

    if (!action.trim()) {
      setError('Please describe your action')
      setSubmitting(false)
      return
    }

    const decision: HumanDecisionRequest = {
      long_term_goals: filteredGoals,
      short_term_priorities: filteredPriorities,
      reasoning: reasoning.trim(),
      action: action.trim(),
    }

    try {
      // Submit via V2 API client
      await apiClient.submitHumanDecision(
        actorName,
        {
          long_term_goals: filteredGoals,
          short_term_priorities: filteredPriorities,
          reasoning: reasoning.trim(),
          action: action.trim(),
        }
      )

      // Clear form
      setGoals([''])
      setPriorities([''])
      setReasoning('')
      setAction('')

      // Notify parent
      onDecisionSubmitted()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Your Turn, {actorName}!</h2>
          <p className="mt-1 text-sm text-gray-600">Turn {currentTurn}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Long-term Goals */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Long-term Goals
            </label>
            <p className="mt-1 text-sm text-gray-500">
              What are your overarching objectives in this scenario?
            </p>
            <div className="mt-2 space-y-2">
              {goals.map((goal, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={goal}
                    onChange={(e) => updateGoal(index, e.target.value)}
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., Ensure AI safety regulations are implemented"
                  />
                  {goals.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeGoal(index)}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addGoal}
              className="mt-2 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              + Add Goal
            </button>
          </div>

          {/* Short-term Priorities */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Short-term Priorities
            </label>
            <p className="mt-1 text-sm text-gray-500">
              What are your immediate priorities for this turn?
            </p>
            <div className="mt-2 space-y-2">
              {priorities.map((priority, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={priority}
                    onChange={(e) => updatePriority(index, e.target.value)}
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., Build coalition with US and EU representatives"
                  />
                  {priorities.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removePriority(index)}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addPriority}
              className="mt-2 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              + Add Priority
            </button>
          </div>

          {/* Reasoning */}
          <div>
            <label htmlFor="reasoning" className="block text-sm font-medium text-gray-700">
              Reasoning
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Explain your strategic thinking and why you're taking this action
            </p>
            <textarea
              id="reasoning"
              rows={4}
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Explain your strategic thinking..."
            />
          </div>

          {/* Action */}
          <div>
            <label htmlFor="action" className="block text-sm font-medium text-gray-700">
              Action
            </label>
            <p className="mt-1 text-sm text-gray-500">
              What specific action are you taking this turn?
            </p>
            <textarea
              id="action"
              rows={4}
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Describe your action in detail..."
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Submitting...' : 'Submit Decision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
