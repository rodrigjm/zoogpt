import { useEffect, useState } from 'react'
import { feedbackApi } from '../../api/client'
import type { FeedbackStats } from '../../types'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function StatCard({
  title,
  value,
  subtitle,
  highlight,
}: {
  title: string
  value: string | number
  subtitle?: string
  highlight?: boolean
}) {
  return (
    <div className={`bg-white rounded-lg shadow p-6 ${highlight ? 'ring-2 ring-red-500' : ''}`}>
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <p className={`mt-2 text-3xl font-bold ${highlight ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
      {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
    </div>
  )
}

export default function FeedbackDashboard() {
  const [stats, setStats] = useState<FeedbackStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await feedbackApi.getStats(7)
        setStats(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load feedback stats')
      } finally {
        setIsLoading(false)
      }
    }
    fetchStats()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading stats...</p>
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

  if (!stats) return null

  const trendData = [...stats.daily_trends].reverse().map((t) => ({
    date: t.date.slice(5), // MM-DD
    total: t.total,
    thumbs_up: t.thumbs_up,
    thumbs_down: t.thumbs_down,
  }))

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <StatCard title="Total Feedback" value={stats.total_count} subtitle="All time" />
        <StatCard title="Thumbs Up" value={stats.thumbs_up_count} subtitle="Positive responses" />
        <StatCard title="Thumbs Down" value={stats.thumbs_down_count} subtitle="Negative responses" />
        <StatCard
          title="Positive Rate"
          value={`${(stats.positive_rate * 100).toFixed(1)}%`}
          subtitle="Satisfaction rate"
        />
        <StatCard
          title="Flagged Items"
          value={stats.flagged_count}
          subtitle="Needs review"
          highlight={stats.flagged_count > 0}
        />
      </div>

      {/* Trend Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Feedback Trends (7 Days)</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="thumbs_up" stroke="#22c55e" name="Thumbs Up" />
              <Line type="monotone" dataKey="thumbs_down" stroke="#ef4444" name="Thumbs Down" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
