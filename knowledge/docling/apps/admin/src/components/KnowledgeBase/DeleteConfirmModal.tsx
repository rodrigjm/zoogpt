import { useState } from 'react'
import type { Animal } from '../../types'

interface DeleteConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
  animal: Animal | null
}

export default function DeleteConfirmModal({ isOpen, onClose, onConfirm, animal }: DeleteConfirmModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConfirm = async () => {
    setIsDeleting(true)
    setError(null)
    try {
      await onConfirm()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete animal')
    } finally {
      setIsDeleting(false)
    }
  }

  if (!isOpen || !animal) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Delete Animal</h2>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-gray-700 mb-2">
              Are you sure you want to delete <strong>{animal.display_name}</strong>?
            </p>
            {animal.source_count > 0 && (
              <p className="text-sm text-red-600 bg-red-50 p-2 rounded">
                This will also delete {animal.source_count} source{animal.source_count !== 1 ? 's' : ''} and all
                associated chunks.
              </p>
            )}
            <p className="text-sm text-gray-500 mt-2">This action cannot be undone.</p>
          </div>

          {error && (
            <div className="mb-4 text-red-500 text-sm bg-red-50 p-2 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isDeleting}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={isDeleting}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {isDeleting ? 'Deleting...' : 'Delete Animal'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
