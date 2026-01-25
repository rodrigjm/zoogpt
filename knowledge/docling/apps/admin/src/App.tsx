import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Sessions from './pages/Sessions'
import Interactions from './pages/Interactions'
import KnowledgeBase from './pages/KnowledgeBase'
import Images from './pages/Images'
import Configuration from './pages/Configuration'
import Feedback from './pages/Feedback'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/sessions" element={<Sessions />} />
                <Route path="/interactions" element={<Interactions />} />
                <Route path="/knowledge-base" element={<KnowledgeBase />} />
                <Route path="/images" element={<Images />} />
                <Route path="/feedback" element={<Feedback />} />
                <Route path="/configuration" element={<Configuration />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
