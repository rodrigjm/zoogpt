import { useEffect, useState } from 'react'
import { analyticsApi } from '../api/client'
import type { SessionSummary, InteractionDetail } from '../types'
import { format } from 'date-fns'

export default function Sessions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [total, setTotal] = useState(0)
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [interactions, setInteractions] = useState<InteractionDetail[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSessions() {
      try {
        const data = await analyticsApi.getSessions({ limit: 50 })
        setSessions(data.sessions)
        setTotal(data.total)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sessions')
      } finally {
        setIsLoading(false)
      }
    }
    fetchSessions()
  }, [])

  const handleSelectSession = async (sessionId: string) => {
    setSelectedSession(sessionId)
    try {
      const data = await analyticsApi.getSessionInteractions(sessionId)
      setInteractions(data.interactions)
    } catch (err) {
      console.error('Failed to load interactions:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading sessions...</p>
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Sessions</h1>
        <p className="text-gray-500">Browse chat sessions ({total} total)</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sessions List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b">
            <h3 className="font-medium">Session List</h3>
          </div>
          <ul className="divide-y max-h-[600px] overflow-auto">
            {sessions.map((session) => (
              <li
                key={session.session_id}
                onClick={() => handleSelectSession(session.session_id)}
                className={`p-4 cursor-pointer hover:bg-gray-50 ${
                  selectedSession === session.session_id ? 'bg-primary-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-mono text-sm text-gray-600">
                      {session.session_id.slice(0, 8)}...
                    </p>
                    <p className="text-sm text-gray-500">
                      {format(new Date(session.start_time), 'MMM d, h:mm a')}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{session.message_count} messages</p>
                    {session.duration_seconds && (
                      <p className="text-sm text-gray-500">
                        {Math.round(session.duration_seconds / 60)} min
                      </p>
                    )}
                  </div>
                </div>
              </li>
            ))}
            {sessions.length === 0 && (
              <li className="p-4 text-gray-500">No sessions yet</li>
            )}
          </ul>
        </div>

        {/* Session Details */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b">
            <h3 className="font-medium">
              {selectedSession ? 'Session Details' : 'Select a session'}
            </h3>
          </div>
          <div className="p-4 max-h-[600px] overflow-auto">
            {selectedSession ? (
              <div className="space-y-4">
                {interactions.map((interaction) => (
                  <div key={interaction.id} className="space-y-2">
                    <div className="bg-blue-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">User</p>
                      <p>{interaction.question}</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">
                        Zoocari ({interaction.latency_ms}ms)
                      </p>
                      <p className="whitespace-pre-wrap">{interaction.answer}</p>
                      {interaction.confidence_score && (
                        <p className="text-xs text-gray-500 mt-2">
                          Confidence: {(interaction.confidence_score * 100).toFixed(0)}%
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                {interactions.length === 0 && (
                  <p className="text-gray-500">No interactions in this session</p>
                )}
              </div>
            ) : (
              <p className="text-gray-500">Click a session to view details</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
