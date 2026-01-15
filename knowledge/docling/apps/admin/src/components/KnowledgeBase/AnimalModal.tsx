import { useState, useEffect } from 'react'
import type { Animal } from '../../types'

interface AnimalModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: { name: string; display_name: string; category?: string; is_active?: boolean }) => Promise<void>
  animal?: Animal | null
  existingNames?: string[]
}

export default function AnimalModal({ isOpen, onClose, onSave, animal, existingNames = [] }: AnimalModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    category: '',
    is_active: true,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const isEditMode = !!animal

  useEffect(() => {
    if (isOpen) {
      if (animal) {
        setFormData({
          name: animal.name,
          display_name: animal.display_name,
          category: animal.category || '',
          is_active: animal.is_active,
        })
      } else {
        setFormData({
          name: '',
          display_name: '',
          category: '',
          is_active: true,
        })
      }
      setErrors({})
    }
  }, [isOpen, animal])

  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    } else if (!isEditMode && existingNames.includes(formData.name.toLowerCase())) {
      newErrors.name = 'An animal with this name already exists'
    }

    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Display name is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    setIsSubmitting(true)
    try {
      const payload: any = {
        display_name: formData.display_name.trim(),
        category: formData.category.trim() || undefined,
      }

      if (!isEditMode) {
        payload.name = formData.name.trim()
      }

      if (isEditMode) {
        payload.is_active = formData.is_active
      }

      await onSave(payload)
      onClose()
    } catch (err) {
      setErrors({ submit: err instanceof Error ? err.message : 'Failed to save animal' })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            {isEditMode ? 'Edit Animal' : 'Add New Animal'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={isEditMode}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                } ${isEditMode ? 'bg-gray-100' : ''}`}
                placeholder="e.g., elephant"
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
              {isEditMode && <p className="text-gray-500 text-xs mt-1">Name cannot be changed</p>}
            </div>

            {/* Display Name */}
            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-1">
                Display Name <span className="text-red-500">*</span>
              </label>
              <input
                id="display_name"
                type="text"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.display_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., Elephant"
              />
              {errors.display_name && <p className="text-red-500 text-sm mt-1">{errors.display_name}</p>}
            </div>

            {/* Category */}
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <input
                id="category"
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g., Mammal"
              />
            </div>

            {/* Is Active (only for edit mode) */}
            {isEditMode && (
              <div className="flex items-center">
                <input
                  id="is_active"
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                  Active
                </label>
              </div>
            )}

            {errors.submit && (
              <div className="text-red-500 text-sm bg-red-50 p-2 rounded">{errors.submit}</div>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {isSubmitting ? 'Saving...' : isEditMode ? 'Save Changes' : 'Create Animal'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
