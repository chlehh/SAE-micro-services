import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import Navbar from './Navbar.jsx'

export default function Protected({ role, children }) {
  const { user } = useAuth()

  if (!user) return <Navigate to="/" replace />
  if (role && user.role !== role) {
    return <Navigate to={user.role === 'agent' ? '/agent' : '/client'} replace />
  }

  return (
    <>
      <Navbar />
      {children}
    </>
  )
}
