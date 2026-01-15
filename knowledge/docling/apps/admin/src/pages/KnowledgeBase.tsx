import { useEffect, useState } from 'react'
import { kbApi } from '../api/client'
import type { Animal, IndexStatus } from '../types'

export default function KnowledgeBase() {
  const [animals, setAnimals] = useState<Animal[]>([])
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRebuilding, setIsRebuilding] = useState(false)

  useEffect(() => {
    async function fetchData() {
      try {
        const [animalsData, statusData] = await Promise.all([
          kbApi.getAnimals({ limit: 100 }),
          kbApi.getIndexStatus(),
        ])
        setAnimals(animalsData.animals)
        setIndexStatus(statusData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load knowledge base')
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleRebuildIndex = async () => {
    setIsRebuilding(true)
    try {
      await kbApi.rebuildIndex()
      // Refresh status
      const status = await kbApi.getIndexStatus()
      setIndexStatus(status)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start rebuild')
    } finally {
      setIsRebuilding(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading knowledge base...</p>
      </div>
    )
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
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-500">Manage animals and source documents</p>
        </div>
        <button
          onClick={handleRebuildIndex}
          disabled={isRebuilding || indexStatus?.status === 'rebuilding'}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {isRebuilding || indexStatus?.status === 'rebuilding'
            ? 'Rebuilding...'
            : 'Rebuild Index'}
        </button>
      </div>

      {/* Index Status */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-4">
          <div
            className={`w-3 h-3 rounded-full ${
              indexStatus?.status === 'ready'
                ? 'bg-green-500'
                : indexStatus?.status === 'rebuilding'
                ? 'bg-yellow-500 animate-pulse'
                : 'bg-red-500'
            }`}
          />
          <div>
            <p className="font-medium">
              Index Status:{' '}
              <span className="capitalize">{indexStatus?.status || 'unknown'}</span>
            </p>
            <p className="text-sm text-gray-500">
              {indexStatus?.document_count || 0} documents, {indexStatus?.chunk_count || 0} chunks
              {indexStatus?.last_rebuild && (
                <> | Last rebuilt: {new Date(indexStatus.last_rebuild).toLocaleString()}</>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Animals Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center">
          <h3 className="font-medium">Animals ({animals.length})</h3>
          <button className="text-sm text-primary-600 hover:text-primary-700">
            + Add Animal
          </button>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Animal
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Sources
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {animals.map((animal) => (
              <tr key={animal.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <p className="font-medium text-gray-900">{animal.display_name}</p>
                  <p className="text-sm text-gray-500">{animal.name}</p>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {animal.category || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {animal.source_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      animal.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {animal.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button className="text-primary-600 hover:text-primary-700 mr-3">
                    Edit
                  </button>
                  <button className="text-red-600 hover:text-red-700">Delete</button>
                </td>
              </tr>
            ))}
            {animals.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  No animals in knowledge base
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
