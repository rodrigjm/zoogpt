import { useEffect, useState } from 'react'
import { feedbackApi } from '../../api/client'
import type { FeedbackItem } from '../../types'
import { format } from 'date-fns'

export default function FeedbackTable() {
  const [items, setItems] = useState<FeedbackItem[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [flaggedFilter, setFlaggedFilter] = useState<boolean | undefined>(undefined)
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)

  useEffect(() => {
    async function fetchFeedback() {
      setIsLoading(true)
      try {
        const params: { type?: string; flagged?: boolean; limit: number; offset: number } = {
          limit,
          offset,
        }
        if (typeFilter) params.type = typeFilter
        if (flaggedFilter !== undefined) params.flagged = flaggedFilter

        const data = await feedbackApi.getList(params)
        setItems(data.items)
        setTotal(data.total)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load feedback')
      } finally {
        setIsLoading(false)
      }
    }
    fetchFeedback()
  }, [typeFilter, flaggedFilter, limit, offset])

  const handleToggleFlag = async (id: number) => {
    try {
      const updated = await feedbackApi.toggleFlag(id)
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)))
    } catch (err) {
      console.error('Failed to toggle flag:', err)
    }
  }

  const handleMarkReviewed = async (id: number) => {
    try {
      const updated = await feedbackApi.markReviewed(id)
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)))
    } catch (err) {
      console.error('Failed to mark reviewed:', err)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'thumbs_up':
        return '👍'
      case 'thumbs_down':
        return '👎'
      case 'comment':
        return '💬'
      default:
        return '❓'
    }
  }

  const truncate = (text: string | null, length: number) => {
    if (!text) return 'N/A'
    return text.length > length ? text.slice(0, length) + '...' : text
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value)
                setOffset(0)
              }}
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="">All Types</option>
              <option value="thumbs_up">Thumbs Up</option>
              <option value="thumbs_down">Thumbs Down</option>
              <option value="comment">Comments</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Flagged</label>
            <select
              value={flaggedFilter === undefined ? '' : flaggedFilter ? 'true' : 'false'}
              onChange={(e) => {
                if (e.target.value === '') {
                  setFlaggedFilter(undefined)
                } else {
                  setFlaggedFilter(e.target.value === 'true')
                }
                setOffset(0)
              }}
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="">All</option>
              <option value="true">Flagged Only</option>
              <option value="false">Not Flagged</option>
            </select>
          </div>
          <div className="flex-1 text-right text-sm text-gray-600 self-end pb-2">
            {total} total items
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Loading feedback...</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Message</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Comment</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Flagged</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {items.map((item) => (
                <>
                  <tr
                    key={item.id}
                    className={`hover:bg-gray-50 cursor-pointer ${
                      item.flagged ? 'bg-red-50' : ''
                    } ${item.reviewed ? 'opacity-50' : ''}`}
                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(item.created_at), 'MMM d, h:mm a')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="text-2xl">{getTypeIcon(item.type)}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                      {truncate(item.message_context, 60)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs">
                      {truncate(item.comment, 40)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleToggleFlag(item.id)
                        }}
                        className={`px-3 py-1 rounded text-xs font-medium ${
                          item.flagged
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {item.flagged ? 'Flagged' : 'Flag'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleMarkReviewed(item.id)
                        }}
                        disabled={item.reviewed}
                        className={`px-3 py-1 rounded text-xs font-medium ${
                          item.reviewed
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-primary-600 text-white hover:bg-primary-700'
                        }`}
                      >
                        {item.reviewed ? 'Reviewed' : 'Mark Reviewed'}
                      </button>
                    </td>
                  </tr>
                  {expandedId === item.id && (
                    <tr>
                      <td colSpan={6} className="px-6 py-4 bg-gray-50">
                        <div className="space-y-2 text-sm">
                          <div>
                            <strong className="text-gray-700">Session ID:</strong>
                            <span className="ml-2 font-mono text-gray-600">{item.session_id}</span>
                          </div>
                          {item.interaction_id && (
                            <div>
                              <strong className="text-gray-700">Interaction ID:</strong>
                              <span className="ml-2 text-gray-600">{item.interaction_id}</span>
                            </div>
                          )}
                          <div>
                            <strong className="text-gray-700">Full Message Context:</strong>
                            <p className="mt-1 text-gray-600">{item.message_context || 'N/A'}</p>
                          </div>
                          {item.comment && (
                            <div>
                              <strong className="text-gray-700">Full Comment:</strong>
                              <p className="mt-1 text-gray-600">{item.comment}</p>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No feedback found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            {offset + 1} - {Math.min(offset + limit, total)} of {total}
          </span>
          <button
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= total}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
