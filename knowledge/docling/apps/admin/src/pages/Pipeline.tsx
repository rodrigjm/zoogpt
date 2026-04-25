import { useState, useEffect, useCallback } from 'react'
import { pipelineApi } from '../api/client'
import StageCard from '../components/Pipeline/StageCard'
import CostProjection from '../components/Pipeline/CostProjection'
import type { PipelineConfig, BenchmarkResult, AvailableModels } from '../types'

export default function Pipeline() {
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [models, setModels] = useState<AvailableModels>({})
  const [sttBenchmark, setSttBenchmark] = useState<BenchmarkResult | null>(null)
  const [llmBenchmark, setLlmBenchmark] = useState<BenchmarkResult | null>(null)
  const [ttsBenchmark, setTtsBenchmark] = useState<BenchmarkResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = useCallback(async () => {
    try {
      const [configData, modelsData, sttLatest, llmLatest, ttsLatest] = await Promise.all([
        pipelineApi.getConfig(),
        pipelineApi.getAvailableModels(),
        pipelineApi.getLatestBenchmark('stt').catch(() => null),
        pipelineApi.getLatestBenchmark('llm').catch(() => null),
        pipelineApi.getLatestBenchmark('tts').catch(() => null),
      ])

      setConfig(configData)
      setModels(modelsData)
      setSttBenchmark(sttLatest)
      setLlmBenchmark(llmLatest)
      setTtsBenchmark(ttsLatest)
      setError('')
    } catch (err: any) {
      setError(err.message || 'Failed to load pipeline configuration')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading pipeline configuration...</div>
      </div>
    )
  }

  if (error || !config) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <div className="text-red-400">{error || 'Failed to load configuration'}</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Pipeline Management</h1>
        <span className="bg-green-900 text-green-300 px-3 py-1 rounded-full text-xs">
          ● All Services Healthy
        </span>
      </div>

      <div className="flex gap-4 flex-wrap mb-6">
        <StageCard
          stage="stt"
          title="Speech-to-Text"
          label="STT"
          config={config.stt}
          models={models.stt || {}}
          latestBenchmark={sttBenchmark}
          onConfigChange={loadData}
        />
        <StageCard
          stage="llm"
          title="LLM / RAG"
          label="LLM"
          config={config.llm}
          models={models.llm || {}}
          latestBenchmark={llmBenchmark}
          onConfigChange={loadData}
        />
        <StageCard
          stage="tts"
          title="Text-to-Speech"
          label="TTS"
          config={config.tts}
          models={models.tts || {}}
          latestBenchmark={ttsBenchmark}
          onConfigChange={loadData}
        />
      </div>

      <CostProjection
        sttBenchmark={sttBenchmark}
        llmBenchmark={llmBenchmark}
        ttsBenchmark={ttsBenchmark}
      />
    </div>
  )
}
