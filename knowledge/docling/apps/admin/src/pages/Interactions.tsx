import { useEffect, useState } from 'react'
import { analyticsApi } from '../api/client'
import type { InteractionDetail } from '../types'
import { format } from 'date-fns'

export default function Interactions() {
  const [interactions, setInteractions] = useState<InteractionDetail[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchInteractions = async (searchQuery?: string) => {
    setIsLoading(true)
    try {
      const data = await analyticsApi.searchInteractions({
        search: searchQuery || undefined,
        limit: 50,
      })
      setInteractions(data.interactions)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load interactions')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchInteractions()
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchInteractions(search)
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Q&A Pairs</h1>
        <p className="text-gray-500">Search and analyze chat interactions ({total} total)</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search questions or answers..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
        />
        <button
          type="submit"
          className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Search
        </button>
      </form>

      {/* Interactions Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Question
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Answer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Latency
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {interactions.map((interaction) => (
                <tr key={interaction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(interaction.timestamp), 'MMM d, h:mm a')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                    {interaction.question}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">
                    {interaction.answer.slice(0, 100)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {interaction.confidence_score ? (
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          interaction.confidence_score > 0.7
                            ? 'bg-green-100 text-green-800'
                            : interaction.confidence_score > 0.4
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {(interaction.confidence_score * 100).toFixed(0)}%
                      </span>
                    ) : (
                      <span className="text-gray-400">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {interaction.latency_ms}ms
                  </td>
                </tr>
              ))}
              {interactions.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No interactions found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
