interface Props {
  images: string[]
  selected: string
  onChange: (url: string) => void
}

export default function ThumbnailSelector({ images, selected, onChange }: Props) {
  if (images.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">Thumbnail</label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
      >
        {images.map((url) => (
          <option key={url} value={url}>
            {url.split('/').pop()}
          </option>
        ))}
      </select>
    </div>
  )
}
