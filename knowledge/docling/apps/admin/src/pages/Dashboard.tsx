import { useEffect, useState } from 'react'
import { analyticsApi } from '../api/client'
import type { DashboardData, LatencyBreakdown } from '../types'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'

function MetricCard({
  title,
  value,
  subtitle,
}: {
  title: string
  value: string | number
  subtitle?: string
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [latency, setLatency] = useState<LatencyBreakdown | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [dashboardData, latencyData] = await Promise.all([
          analyticsApi.getDashboard(7),
          analyticsApi.getLatencyBreakdown(7),
        ])
        setData(dashboardData)
        setLatency(latencyData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  if (!data) return null

  const trendData = [...data.trends].reverse().map((t) => ({
    date: t.date.slice(5), // MM-DD
    sessions: t.sessions,
    questions: t.questions,
  }))

  const latencyData = latency
    ? [
        { name: 'RAG', p50: latency.rag.p50, p90: latency.rag.p90 },
        { name: 'LLM', p50: latency.llm.p50, p90: latency.llm.p90 },
        { name: 'TTS', p50: latency.tts.p50, p90: latency.tts.p90 },
      ]
    : []

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Overview of Zoocari chatbot analytics</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Sessions Today"
          value={data.today.sessions}
          subtitle="Unique conversations"
        />
        <MetricCard
          title="Questions Today"
          value={data.today.questions}
          subtitle="Total Q&A pairs"
        />
        <MetricCard
          title="Avg Response Time"
          value={data.today.avg_latency_ms ? `${Math.round(data.today.avg_latency_ms)}ms` : 'N/A'}
          subtitle="End-to-end latency"
        />
        <MetricCard
          title="Error Rate"
          value={`${(data.today.error_rate * 100).toFixed(1)}%`}
          subtitle="Low confidence responses"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trends Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Usage Trends (7 Days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="sessions" stroke="#22c55e" name="Sessions" />
                <Line type="monotone" dataKey="questions" stroke="#3b82f6" name="Questions" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Response Time Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v) => `${v}ms`} />
                <Bar dataKey="p50" fill="#22c55e" name="P50" />
                <Bar dataKey="p90" fill="#f59e0b" name="P90" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Lists Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Questions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Questions</h3>
          <ul className="space-y-3">
            {data.top_questions.slice(0, 5).map((q, i) => (
              <li key={i} className="flex items-center justify-between">
                <span className="text-gray-600 truncate flex-1">{q.question}</span>
                <span className="ml-4 text-sm font-medium text-gray-900 bg-gray-100 px-2 py-1 rounded">
                  {q.count}
                </span>
              </li>
            ))}
            {data.top_questions.length === 0 && (
              <li className="text-gray-500">No questions yet</li>
            )}
          </ul>
        </div>

        {/* Top Animals */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Most Queried Animals</h3>
          <ul className="space-y-3">
            {data.top_animals.slice(0, 5).map((a, i) => (
              <li key={i} className="flex items-center justify-between">
                <span className="text-gray-600">{a.name}</span>
                <span className="text-sm font-medium text-gray-900 bg-gray-100 px-2 py-1 rounded">
                  {a.count}
                </span>
              </li>
            ))}
            {data.top_animals.length === 0 && (
              <li className="text-gray-500">No data yet</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}
