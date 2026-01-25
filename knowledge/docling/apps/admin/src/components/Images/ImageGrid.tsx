import { useState } from 'react'
import type { AnimalImageConfig } from '../../types'
import ImageCard from './ImageCard'
import ImageDetailModal from './ImageDetailModal'

interface Props {
  animals: Record<string, AnimalImageConfig>
  onRefresh: () => void
}

export default function ImageGrid({ animals, onRefresh }: Props) {
  const [selectedAnimal, setSelectedAnimal] = useState<string | null>(null)
  const sortedAnimals = Object.entries(animals).sort(([a], [b]) => a.localeCompare(b))

  const handleSave = () => {
    setSelectedAnimal(null)
    onRefresh()
  }

  if (sortedAnimals.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No animal images found</p>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {sortedAnimals.map(([name, config]) => (
          <ImageCard
            key={name}
            name={name}
            config={config}
            onRefresh={onRefresh}
            onSelect={setSelectedAnimal}
          />
        ))}
      </div>

      {selectedAnimal && (
        <ImageDetailModal
          name={selectedAnimal}
          onClose={() => setSelectedAnimal(null)}
          onSave={handleSave}
        />
      )}
    </>
  )
}
