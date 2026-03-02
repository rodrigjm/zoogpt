interface Props {
  images: string[]
  selectedThumbnail: string
  onDelete: (url: string) => void
  onSelectThumbnail: (url: string) => void
}

export default function ImageGallery({ images, selectedThumbnail, onDelete, onSelectThumbnail }: Props) {
  if (images.length === 0) {
    return <div className="text-center py-8 text-gray-500">No images yet</div>
  }

  const isThumbnail = (url: string) => {
    const filename = url.split('/').pop()?.replace('.webp', '') || ''
    return selectedThumbnail.includes(filename)
  }

  return (
    <div className="grid grid-cols-3 gap-3">
      {images.map((url) => (
        <div key={url} className="relative group aspect-video bg-gray-100 rounded overflow-hidden">
          <img
            src={url}
            alt=""
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-animal.png'
            }}
          />

          {isThumbnail(url) && (
            <span className="absolute top-1 left-1 bg-green-500 text-white text-xs px-2 py-1 rounded font-medium">
              Thumbnail
            </span>
          )}

          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <button
              onClick={() => onSelectThumbnail(url)}
              className="px-3 py-1.5 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
            >
              Set Thumbnail
            </button>
            <button
              onClick={() => onDelete(url)}
              className="px-3 py-1.5 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
