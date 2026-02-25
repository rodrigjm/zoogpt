import { useEffect, useState, useCallback, useRef } from 'react'
import { kbApi } from '../api/client'
import type { Animal, IndexStatus, IndexPendingStatus } from '../types'
import { AnimalModal, DeleteConfirmModal, SourcesPanel } from '../components/KnowledgeBase'

export default function KnowledgeBase() {
  const [animals, setAnimals] = useState<Animal[]>([])
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [pendingStatus, setPendingStatus] = useState<IndexPendingStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRebuilding, setIsRebuilding] = useState(false)
  const [rebuildToast, setRebuildToast] = useState<string | null>(null)
  const prevStatusRef = useRef<string | null>(null)

  // Modal states
  const [isAnimalModalOpen, setIsAnimalModalOpen] = useState(false)
  const [editingAnimal, setEditingAnimal] = useState<Animal | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [deletingAnimal, setDeletingAnimal] = useState<Animal | null>(null)
  const [isSourcesPanelOpen, setIsSourcesPanelOpen] = useState(false)
  const [selectedAnimalId, setSelectedAnimalId] = useState<number | null>(null)
  const [selectedAnimalName, setSelectedAnimalName] = useState('')

  // Fetch pending status
  const fetchPendingStatus = useCallback(async () => {
    try {
      const pending = await kbApi.getIndexPending()
      setPendingStatus(pending)
    } catch {
      // Silent fail for pending status
    }
  }, [])

  // Fetch index status
  const fetchIndexStatus = useCallback(async () => {
    try {
      const status = await kbApi.getIndexStatus()
      // Check for transition from rebuilding to ready/failed
      if (prevStatusRef.current === 'rebuilding' && status.status !== 'rebuilding') {
        if (status.status === 'ready') {
          setRebuildToast('Index rebuild completed successfully!')
          setTimeout(() => setRebuildToast(null), 5000)
        }
        setIsRebuilding(false)
      }
      prevStatusRef.current = status.status
      setIndexStatus(status)
    } catch {
      // Silent fail for status polling
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [])

  // Poll for pending changes every 5 seconds
  useEffect(() => {
    fetchPendingStatus()
    const interval = setInterval(fetchPendingStatus, 5000)
    return () => clearInterval(interval)
  }, [fetchPendingStatus])

  // Poll during rebuild every 2 seconds
  useEffect(() => {
    if (indexStatus?.status !== 'rebuilding' && !isRebuilding) return

    const poll = setInterval(fetchIndexStatus, 2000)
    return () => clearInterval(poll)
  }, [indexStatus?.status, isRebuilding, fetchIndexStatus])

  async function fetchData() {
    try {
      const [animalsData, statusData] = await Promise.all([
        kbApi.getAnimals({ limit: 200 }),
        kbApi.getIndexStatus(),
      ])
      setAnimals(animalsData.animals)
      setIndexStatus(statusData)
      setError(null)
    } catch (err) {
      console.error('[KnowledgeBase] Failed to load:', err)
      setError(err instanceof Error ? err.message : 'Failed to load knowledge base')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRebuildIndex = async () => {
    setIsRebuilding(true)
    try {
      await kbApi.rebuildIndex()
      // Clear pending status immediately (backend clears it too)
      setPendingStatus({ pending: false, last_change_at: null, auto_rebuild_in_seconds: null })
      // Refresh status
      const status = await kbApi.getIndexStatus()
      setIndexStatus(status)
      prevStatusRef.current = status.status
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start rebuild')
      setIsRebuilding(false)
    }
  }

  const handleAddAnimal = () => {
    setEditingAnimal(null)
    setIsAnimalModalOpen(true)
  }

  const handleEditAnimal = (animal: Animal) => {
    setEditingAnimal(animal)
    setIsAnimalModalOpen(true)
  }

  const handleDeleteAnimal = (animal: Animal) => {
    setDeletingAnimal(animal)
    setIsDeleteModalOpen(true)
  }

  const handleViewSources = (animal: Animal) => {
    setSelectedAnimalId(animal.id)
    setSelectedAnimalName(animal.display_name)
    setIsSourcesPanelOpen(true)
  }

  const handleSaveAnimal = async (data: any) => {
    if (editingAnimal) {
      await kbApi.updateAnimal(editingAnimal.id, data)
    } else {
      await kbApi.createAnimal(data)
    }
    await fetchData()
  }

  const handleConfirmDelete = async () => {
    if (deletingAnimal) {
      await kbApi.deleteAnimal(deletingAnimal.id)
      await fetchData()
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
      {/* Success Toast */}
      {rebuildToast && (
        <div className="fixed top-4 right-4 z-50 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          {rebuildToast}
        </div>
      )}

      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-500">Manage animals and source documents</p>
        </div>
        <div className="flex items-center gap-2">
          {pendingStatus?.pending && (
            <span className="text-sm text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
              Auto-rebuild in {pendingStatus.auto_rebuild_in_seconds}s
            </span>
          )}
          <button
            onClick={handleRebuildIndex}
            disabled={isRebuilding || indexStatus?.status === 'rebuilding'}
            className={`px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
              pendingStatus?.pending
                ? 'bg-yellow-500 hover:bg-yellow-600 animate-pulse'
                : 'bg-primary-600 hover:bg-primary-700'
            }`}
          >
            {isRebuilding || indexStatus?.status === 'rebuilding'
              ? 'Rebuilding...'
              : pendingStatus?.pending
              ? 'Rebuild Now'
              : 'Rebuild Index'}
          </button>
        </div>
      </div>

      {/* Index Status */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
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
          {pendingStatus?.pending && (
            <div className="flex items-center gap-2 text-sm text-yellow-600">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              <span>Changes pending</span>
            </div>
          )}
        </div>
      </div>

      {/* Animals Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center">
          <h3 className="font-medium">Animals ({animals.length})</h3>
          <button
            onClick={handleAddAnimal}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
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
                <td
                  className="px-6 py-4 whitespace-nowrap cursor-pointer"
                  onClick={() => handleViewSources(animal)}
                >
                  <p className="font-medium text-gray-900">{animal.display_name}</p>
                  <p className="text-sm text-gray-500">{animal.name}</p>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {animal.category || '-'}
                </td>
                <td
                  className="px-6 py-4 whitespace-nowrap text-sm text-primary-600 cursor-pointer hover:text-primary-700"
                  onClick={() => handleViewSources(animal)}
                >
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
                  <button
                    onClick={() => handleEditAnimal(animal)}
                    className="text-primary-600 hover:text-primary-700 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteAnimal(animal)}
                    className="text-red-600 hover:text-red-700"
                  >
                    Delete
                  </button>
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

      {/* Modals */}
      <AnimalModal
        isOpen={isAnimalModalOpen}
        onClose={() => setIsAnimalModalOpen(false)}
        onSave={handleSaveAnimal}
        animal={editingAnimal}
        existingNames={animals.map((a) => a.name.toLowerCase())}
      />

      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleConfirmDelete}
        animal={deletingAnimal}
      />

      <SourcesPanel
        isOpen={isSourcesPanelOpen}
        onClose={() => setIsSourcesPanelOpen(false)}
        animalId={selectedAnimalId}
        animalName={selectedAnimalName}
      />
    </div>
  )
}
