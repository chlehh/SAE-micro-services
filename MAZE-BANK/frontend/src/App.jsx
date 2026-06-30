import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth.jsx'
import Protected from './components/Protected.jsx'
import Auth from './pages/Auth.jsx'
import ClientDashboard from './pages/ClientDashboard.jsx'
import AgentDashboard from './pages/AgentDashboard.jsx'
import Logs from './pages/Logs.jsx'

function Home() {
  const { user } = useAuth()
  if (user) return <Navigate to={user.role === 'agent' ? '/agent' : '/client'} replace />
  return <Auth />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/client" element={<Protected role="client"><ClientDashboard /></Protected>} />
          <Route path="/agent" element={<Protected role="agent"><AgentDashboard /></Protected>} />
          <Route path="/logs" element={<Protected role="agent"><Logs /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
