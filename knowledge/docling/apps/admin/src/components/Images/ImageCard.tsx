import type { AnimalImageConfig } from '../../types'

interface Props {
  name: string
  config: AnimalImageConfig
  onRefresh: () => void
  onSelect: (name: string) => void
}

export default function ImageCard({ name, config, onRefresh: _onRefresh, onSelect }: Props) {
  return (
    <div
      onClick={() => onSelect(name)}
      className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer overflow-hidden"
    >
      <div className="aspect-video bg-gray-100 relative">
        <img
          src={config.thumbnail}
          alt={config.alt}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder-animal.png'
          }}
        />
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
          <span className="text-white text-sm font-medium truncate block">{name}</span>
        </div>
      </div>
      <div className="p-2">
        <p className="text-xs text-gray-500">{config.images.length} image(s)</p>
      </div>
    </div>
  )
}
