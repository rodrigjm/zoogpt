import { FeedbackDashboard, FeedbackTable } from '../components/Feedback'

export default function Feedback() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User Feedback</h1>
        <p className="text-gray-500">Monitor and manage user feedback and ratings</p>
      </div>

      <FeedbackDashboard />
      <FeedbackTable />
    </div>
  )
}
