import { useEffect, useState } from 'react'
import { configApi } from '../api/client'
import type { PromptsConfig, ModelConfig, TTSConfig } from '../types'

export default function Configuration() {
  const [prompts, setPrompts] = useState<PromptsConfig | null>(null)
  const [model, setModel] = useState<ModelConfig | null>(null)
  const [tts, setTts] = useState<TTSConfig | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<string | null>(null)

  useEffect(() => {
    async function fetchConfig() {
      try {
        const [promptsData, modelData, ttsData] = await Promise.all([
          configApi.getPrompts(),
          configApi.getModel(),
          configApi.getTTS(),
        ])
        setPrompts(promptsData)
        setModel(modelData)
        setTts(ttsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load configuration')
      } finally {
        setIsLoading(false)
      }
    }
    fetchConfig()
  }, [])

  const handleSavePrompts = async () => {
    if (!prompts) return
    try {
      await configApi.updatePrompts(prompts)
      setSaveStatus('Prompts saved!')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prompts')
    }
  }

  const handleSaveModel = async () => {
    if (!model) return
    try {
      await configApi.updateModel(model)
      setSaveStatus('Model settings saved!')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save model settings')
    }
  }

  const handleSaveTTS = async () => {
    if (!tts) return
    try {
      await configApi.updateTTS(tts)
      setSaveStatus('TTS settings saved!')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save TTS settings')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading configuration...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configuration</h1>
        <p className="text-gray-500">Manage prompts, model, and voice settings</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {saveStatus && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {saveStatus}
        </div>
      )}

      {/* Prompts Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Prompt Configuration</h3>
          <button
            onClick={handleSavePrompts}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Save Prompts
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt
            </label>
            <textarea
              value={prompts?.system_prompt || ''}
              onChange={(e) => setPrompts((p) => p && { ...p, system_prompt: e.target.value })}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fallback Response
            </label>
            <textarea
              value={prompts?.fallback_response || ''}
              onChange={(e) => setPrompts((p) => p && { ...p, fallback_response: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Model Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Model Settings</h3>
          <button
            onClick={handleSaveModel}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Save Model
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              value={model?.name || 'gpt-4o-mini'}
              onChange={(e) => setModel((m) => m && { ...m, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature ({model?.temperature || 0.7})
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={model?.temperature || 0.7}
              onChange={(e) =>
                setModel((m) => m && { ...m, temperature: parseFloat(e.target.value) })
              }
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Tokens
            </label>
            <input
              type="number"
              min="100"
              max="4000"
              value={model?.max_tokens || 500}
              onChange={(e) =>
                setModel((m) => m && { ...m, max_tokens: parseInt(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* TTS Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Voice Settings</h3>
          <button
            onClick={handleSaveTTS}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Save Voice
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select
              value={tts?.provider || 'kokoro'}
              onChange={(e) =>
                setTts((t) => t && { ...t, provider: e.target.value as 'kokoro' | 'openai' })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="kokoro">Kokoro (Local)</option>
              <option value="openai">OpenAI (Cloud)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Voice</label>
            <select
              value={tts?.default_voice || 'af_heart'}
              onChange={(e) => setTts((t) => t && { ...t, default_voice: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            >
              {tts?.available_voices?.[tts.provider]?.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name} - {voice.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Speed ({tts?.speed || 1.0}x)
            </label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={tts?.speed || 1.0}
              onChange={(e) => setTts((t) => t && { ...t, speed: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
