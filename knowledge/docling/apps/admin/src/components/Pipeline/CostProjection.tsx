import type { BenchmarkResult } from '../../types'

interface CostProjectionProps {
  sttBenchmark: BenchmarkResult | null
  llmBenchmark: BenchmarkResult | null
  ttsBenchmark: BenchmarkResult | null
}

const DAILY_VOLUMES = [500, 1000, 2000, 5000]
const DAYS_PER_MONTH = 30

function formatCost(cost: number): string {
  if (cost === 0) return '$0.00'
  if (cost < 0.01) return '< $0.01'
  return `$${cost.toFixed(2)}`
}

export default function CostProjection({ sttBenchmark, llmBenchmark, ttsBenchmark }: CostProjectionProps) {
  const sttCost = sttBenchmark?.cost_per_request ?? null
  const llmCost = llmBenchmark?.cost_per_request ?? null
  const ttsCost = ttsBenchmark?.cost_per_request ?? null

  const hasBenchmarks = sttCost !== null || llmCost !== null || ttsCost !== null

  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
      <div className="mb-4">
        <div className="text-lg font-semibold text-white">Monthly Cost Projection</div>
        <div className="text-xs text-gray-500">
          Based on current model selection and latest benchmark per-request costs
        </div>
      </div>

      {hasBenchmarks ? (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-2.5 text-gray-500 font-medium">Daily Volume</th>
                <th className="text-right p-2.5 text-blue-400 font-medium">STT</th>
                <th className="text-right p-2.5 text-purple-400 font-medium">LLM/RAG</th>
                <th className="text-right p-2.5 text-orange-400 font-medium">TTS</th>
                <th className="text-right p-2.5 text-white font-semibold">Total / Month</th>
              </tr>
            </thead>
            <tbody>
              {DAILY_VOLUMES.map((volume) => {
                const sttMonthly = sttCost !== null ? sttCost * volume * DAYS_PER_MONTH : null
                const llmMonthly = llmCost !== null ? llmCost * volume * DAYS_PER_MONTH : null
                const ttsMonthly = ttsCost !== null ? ttsCost * volume * DAYS_PER_MONTH : null

                const total = (sttMonthly ?? 0) + (llmMonthly ?? 0) + (ttsMonthly ?? 0)
                const allPresent = sttMonthly !== null && llmMonthly !== null && ttsMonthly !== null

                return (
                  <tr key={volume} className="border-b border-gray-900">
                    <td className="p-2.5 text-gray-300">
                      {volume.toLocaleString()} questions/day
                    </td>
                    <td className="p-2.5 text-right text-blue-300">
                      {sttMonthly !== null ? formatCost(sttMonthly) : '—'}
                    </td>
                    <td className="p-2.5 text-right text-purple-300">
                      {llmMonthly !== null ? formatCost(llmMonthly) : '—'}
                    </td>
                    <td className="p-2.5 text-right text-orange-300">
                      {ttsMonthly !== null ? formatCost(ttsMonthly) : '—'}
                    </td>
                    <td className="p-2.5 text-right text-white font-semibold">
                      {allPresent ? formatCost(total) : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="text-[11px] text-gray-600 mt-2">
            * Local models (Kokoro, faster-whisper, Ollama) show $0.00 API cost — compute/infra cost not included.
          </div>
        </>
      ) : (
        <div className="text-center text-gray-500 text-sm py-8">
          Run benchmarks for each stage to see cost projections
        </div>
      )}
    </div>
  )
}
