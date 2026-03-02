import { useState, useEffect } from 'react'
import { imagesApi } from '../../api/client'
import ImageUploader from './ImageUploader'
import ImageGallery from './ImageGallery'
import ThumbnailSelector from './ThumbnailSelector'

interface Props {
  name: string
  onClose: () => void
  onSave: () => void
}

export default function ImageDetailModal({ name, onClose, onSave }: Props) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [altText, setAltText] = useState('')
  const [selectedThumbnail, setSelectedThumbnail] = useState('')
  const [images, setImages] = useState<string[]>([])

  useEffect(() => {
    loadAnimal()
  }, [name])

  const loadAnimal = async () => {
    try {
      setLoading(true)
      const data = await imagesApi.getAnimal(name)
      setAltText(data.alt)
      setSelectedThumbnail(data.thumbnail)
      setImages(data.images)
    } catch (err) {
      console.error('Failed to load animal:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: File) => {
    try {
      const result = await imagesApi.uploadImage(name, file)
      setImages([...images, result.url])
      if (result.thumbnail_url && !selectedThumbnail) {
        setSelectedThumbnail(result.thumbnail_url)
      }
    } catch (err) {
      console.error('Upload failed:', err)
      throw err
    }
  }

  const handleDelete = async (imageUrl: string) => {
    const filename = imageUrl.split('/').pop()
    if (!filename || !confirm('Delete this image?')) return

    try {
      await imagesApi.deleteImage(name, filename)
      const newImages = images.filter(img => img !== imageUrl)
      setImages(newImages)

      if (selectedThumbnail === imageUrl && newImages.length > 0) {
        setSelectedThumbnail(newImages[0])
      }
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await imagesApi.updateAnimal(name, {
        alt: altText,
        thumbnail: selectedThumbnail,
        images: images,
      })
      onSave()
    } catch (err) {
      console.error('Save failed:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">{name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Alt Text</label>
            <input
              type="text"
              value={altText}
              onChange={(e) => setAltText(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Descriptive text for accessibility"
            />
          </div>

          <ThumbnailSelector
            images={images}
            selected={selectedThumbnail}
            onChange={setSelectedThumbnail}
          />

          <ImageUploader onUpload={handleUpload} />

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Images</label>
            <ImageGallery
              images={images}
              selectedThumbnail={selectedThumbnail}
              onDelete={handleDelete}
              onSelectThumbnail={setSelectedThumbnail}
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 p-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
