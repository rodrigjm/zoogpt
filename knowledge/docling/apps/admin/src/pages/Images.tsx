import { useState, useEffect } from 'react'
import { imagesApi } from '../api/client'
import type { AnimalImageConfig } from '../types'
import ImageGrid from '../components/Images/ImageGrid'

export default function Images() {
  const [animals, setAnimals] = useState<Record<string, AnimalImageConfig>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAnimals()
  }, [])

  const loadAnimals = async () => {
    try {
      setLoading(true)
      const data = await imagesApi.getAnimals()
      setAnimals(data.animals)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load images')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading images...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
        <button onClick={loadAnimals} className="mt-2 text-sm text-red-500 hover:underline">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Animal Images</h1>
          <p className="text-gray-500">{Object.keys(animals).length} animals with images</p>
        </div>
      </div>

      <ImageGrid animals={animals} onRefresh={loadAnimals} />
    </div>
  )
}
