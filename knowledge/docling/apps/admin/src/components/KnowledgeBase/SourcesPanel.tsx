import { useState, useEffect } from 'react'
import { kbApi } from '../../api/client'
import type { AnimalDetail } from '../../types'

interface SourcesPanelProps {
  isOpen: boolean
  onClose: () => void
  animalId: number | null
  animalName: string
}

export default function SourcesPanel({ isOpen, onClose, animalId, animalName }: SourcesPanelProps) {
  const [animalDetail, setAnimalDetail] = useState<AnimalDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAdding, setIsAdding] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)
  const [newSource, setNewSource] = useState({
    title: '',
    url: '',
    content: '',
  })

  useEffect(() => {
    if (isOpen && animalId) {
      loadAnimalDetail()
    }
  }, [isOpen, animalId])

  const loadAnimalDetail = async () => {
    if (!animalId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await kbApi.getAnimal(animalId)
      setAnimalDetail(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!animalId || !newSource.title.trim() || !newSource.content.trim()) return

    setIsAdding(true)
    setError(null)
    try {
      await kbApi.addSource(animalId, {
        title: newSource.title.trim(),
        url: newSource.url.trim() || undefined,
        content: newSource.content.trim(),
      })
      setNewSource({ title: '', url: '', content: '' })
      await loadAnimalDetail()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add source')
    } finally {
      setIsAdding(false)
    }
  }

  const handleDeleteSource = async (sourceId: number) => {
    if (!animalId) return
    setError(null)
    try {
      await kbApi.deleteSource(animalId, sourceId)
      setDeleteConfirm(null)
      await loadAnimalDetail()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete source')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="relative bg-white w-full max-w-2xl h-full shadow-xl overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 z-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Sources for {animalName}</h2>
              <p className="text-sm text-gray-500 mt-1">
                {animalDetail?.sources.length || 0} source{animalDetail?.sources.length !== 1 ? 's' : ''}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-2"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Add Source Form */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Add New Source</h3>
            <form onSubmit={handleAddSource} className="space-y-3">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  value={newSource.title}
                  onChange={(e) => setNewSource({ ...newSource, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Diet and habitat information"
                  required
                />
              </div>

              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
                  URL (optional)
                </label>
                <input
                  id="url"
                  type="url"
                  value={newSource.url}
                  onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="https://..."
                />
              </div>

              <div>
                <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
                  Content <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="content"
                  value={newSource.content}
                  onChange={(e) => setNewSource({ ...newSource, content: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={6}
                  placeholder="Enter the source text or document content..."
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isAdding || !newSource.title.trim() || !newSource.content.trim()}
                className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {isAdding ? 'Adding...' : 'Add Source'}
              </button>
            </form>
          </div>

          {/* Sources List */}
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Loading sources...</div>
          ) : animalDetail?.sources.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No sources yet. Add one above.</div>
          ) : (
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Existing Sources</h3>
              {animalDetail?.sources.map((source) => (
                <div key={source.id} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{source.title}</h4>
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary-600 hover:underline"
                        >
                          {source.url}
                        </a>
                      )}
                    </div>
                    {deleteConfirm === source.id ? (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleDeleteSource(source.id)}
                          className="text-sm px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                          Confirm
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="text-sm px-3 py-1 border border-gray-300 rounded hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirm(source.id)}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                  <div className="flex gap-4 text-sm text-gray-500">
                    <span>{source.chunk_count} chunk{source.chunk_count !== 1 ? 's' : ''}</span>
                    {source.last_indexed && (
                      <span>Indexed: {new Date(source.last_indexed).toLocaleDateString()}</span>
                    )}
                    <span>Added: {new Date(source.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
