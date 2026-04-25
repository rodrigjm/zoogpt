import { useState, useEffect, useRef } from 'react'
import { pipelineApi } from '../../api/client'
import type {
  PipelineStageConfig,
  BenchmarkResult,
  BenchmarkStatus,
  ModelOption,
} from '../../types'

interface StageCardProps {
  stage: 'stt' | 'llm' | 'tts'
  title: string
  label: string
  config: PipelineStageConfig
  models: Record<string, ModelOption[]>
  latestBenchmark: BenchmarkResult | null
  onConfigChange: () => void
}

const STAGE_COLORS: Record<string, { badge: string; badgeText: string; button: string }> = {
  stt: { badge: 'bg-blue-900', badgeText: 'text-blue-300', button: 'bg-blue-900 text-blue-300' },
  llm: { badge: 'bg-purple-900', badgeText: 'text-purple-300', button: 'bg-purple-900 text-purple-300' },
  tts: { badge: 'bg-orange-900', badgeText: 'text-orange-300', button: 'bg-orange-900 text-orange-300' },
}

const CONCURRENCY_OPTIONS = [1, 5, 10, 20, 50]
const ROUND_OPTIONS = [1, 3, 5]

export default function StageCard({
  stage,
  title,
  label,
  config,
  models,
  latestBenchmark,
  onConfigChange,
}: StageCardProps) {
  const [selectedProvider, setSelectedProvider] = useState(config.provider)
  const [selectedModel, setSelectedModel] = useState(config.model || '')
  const [applyStatus, setApplyStatus] = useState<'idle' | 'applying' | 'success' | 'error'>('idle')
  const [applyError, setApplyError] = useState('')
  const [concurrency, setConcurrency] = useState(5)
  const [rounds, setRounds] = useState(3)
  const [benchmarkStatus, setBenchmarkStatus] = useState<BenchmarkStatus | null>(null)
  const pollRef = useRef<number | null>(null)
  const colors = STAGE_COLORS[stage]

  const providerNames = Object.keys(models)

  const handleProviderModelChange = (value: string) => {
    const [prov, ...modelParts] = value.split('/')
    const model = modelParts.join('/')
    setSelectedProvider(prov)
    setSelectedModel(model)
    setApplyStatus('idle')
  }

  const currentValue = `${selectedProvider}/${selectedModel}`

  const handleApply = async () => {
    setApplyStatus('applying')
    setApplyError('')
    try {
      await pipelineApi.updateStage(stage, {
        provider: selectedProvider,
        model: selectedModel || null,
      })
      setApplyStatus('success')
      onConfigChange()
      setTimeout(() => setApplyStatus('idle'), 3000)
    } catch (err: any) {
      setApplyStatus('error')
      setApplyError(err.message || 'Failed to apply')
    }
  }

  const handleRunBenchmark = async () => {
    try {
      const status = await pipelineApi.startBenchmark(stage, { concurrency, rounds })
      setBenchmarkStatus(status)
      startPolling()
    } catch (err: any) {
      alert(err.message || 'Failed to start benchmark')
    }
  }

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = window.setInterval(async () => {
      try {
        const status = await pipelineApi.getBenchmarkStatus(stage)
        setBenchmarkStatus(status)
        if (!status.running) {
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          onConfigChange()
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current)
        pollRef.current = null
      }
    }, 1000)
  }

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const stageNumber = stage === 'stt' ? 1 : stage === 'llm' ? 2 : 3

  return (
    <div className="flex-1 min-w-[280px] bg-gray-800 rounded-xl p-5 border border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wider">Stage {stageNumber}</div>
          <div className="text-lg font-semibold text-white">{title}</div>
        </div>
        <div className={`${colors.badge} ${colors.badgeText} px-3 py-1 rounded-lg text-xs font-medium`}>
          {label}
        </div>
      </div>

      <div className="mb-4">
        <div className="text-xs text-gray-400 mb-1">Provider / Model</div>
        <div className="flex gap-2">
          <select
            value={currentValue}
            onChange={(e) => handleProviderModelChange(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-600 text-white p-2 rounded-md text-sm"
          >
            {providerNames.map((prov) => (
              <optgroup key={prov} label={prov}>
                {models[prov].map((m) => (
                  <option key={`${prov}/${m.id}`} value={`${prov}/${m.id}`}>
                    {m.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <button
            onClick={handleApply}
            disabled={applyStatus === 'applying'}
            className="bg-green-800 text-white px-4 py-2 rounded-md text-xs hover:bg-green-700 disabled:opacity-50"
          >
            {applyStatus === 'applying' ? '...' : 'Apply'}
          </button>
        </div>
        <div className="text-xs mt-1">
          {applyStatus === 'success' && <span className="text-green-400">&#10003; Active — applied at runtime</span>}
          {applyStatus === 'error' && <span className="text-red-400">&#10007; {applyError}</span>}
          {applyStatus === 'idle' && <span className="text-green-400">&#10003; Active</span>}
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg p-3 mb-3">
        {latestBenchmark ? (
          <>
            <div className="text-xs text-gray-500 mb-2">
              Last Benchmark — {new Date(latestBenchmark.timestamp).toLocaleDateString()}
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-lg font-semibold text-blue-300">
                  {latestBenchmark.metrics.p50_ms < 1000
                    ? `${Math.round(latestBenchmark.metrics.p50_ms)}ms`
                    : `${(latestBenchmark.metrics.p50_ms / 1000).toFixed(1)}s`}
                </div>
                <div className="text-[10px] text-gray-500">p50 latency</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-yellow-300">
                  {latestBenchmark.metrics.p95_ms < 1000
                    ? `${Math.round(latestBenchmark.metrics.p95_ms)}ms`
                    : `${(latestBenchmark.metrics.p95_ms / 1000).toFixed(1)}s`}
                </div>
                <div className="text-[10px] text-gray-500">p95 latency</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-green-400">
                  ${latestBenchmark.cost_per_request.toFixed(4)}
                </div>
                <div className="text-[10px] text-gray-500">per request</div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-xs text-gray-500 text-center py-2">
            No benchmark data — run a benchmark to see metrics
          </div>
        )}
      </div>

      {benchmarkStatus?.running ? (
        <div className="text-center">
          <div className="text-sm text-blue-300 mb-1">Running...</div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{
                width: `${benchmarkStatus.total_requests > 0
                  ? (benchmarkStatus.completed_requests / benchmarkStatus.total_requests) * 100
                  : 0}%`,
              }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">{benchmarkStatus.progress}</div>
        </div>
      ) : (
        <div className="flex gap-2 items-center">
          <select
            value={concurrency}
            onChange={(e) => setConcurrency(Number(e.target.value))}
            className="bg-gray-900 border border-gray-600 text-white p-1.5 rounded-md text-xs"
          >
            {CONCURRENCY_OPTIONS.map((c) => (
              <option key={c} value={c}>{c} user{c > 1 ? 's' : ''}</option>
            ))}
          </select>
          <select
            value={rounds}
            onChange={(e) => setRounds(Number(e.target.value))}
            className="bg-gray-900 border border-gray-600 text-white p-1.5 rounded-md text-xs"
          >
            {ROUND_OPTIONS.map((r) => (
              <option key={r} value={r}>{r} round{r > 1 ? 's' : ''}</option>
            ))}
          </select>
          <button
            onClick={handleRunBenchmark}
            className={`${colors.button} px-3 py-1.5 rounded-md text-xs hover:opacity-80`}
          >
            &#9654; Run
          </button>
        </div>
      )}
    </div>
  )
}
