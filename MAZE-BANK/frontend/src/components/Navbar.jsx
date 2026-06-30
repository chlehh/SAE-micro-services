import { NavLink, useNavigate } from 'react-router-dom'
import Logo from './Logo.jsx'
import { useAuth } from '../auth.jsx'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="navbar">
      <Logo size={22} />
      <div className="links">
        {user?.role === 'client' && <NavLink to="/client">Mes comptes</NavLink>}
        {user?.role === 'agent' && <NavLink to="/agent">Validation</NavLink>}
        {user?.role === 'agent' && <NavLink to="/logs">Journaux</NavLink>}
      </div>
      <div className="user">
        {user && (
          <>
            <span>
              {user.full_name} <span className="badge role">{user.role}</span>
            </span>
            <button className="btn ghost sm" onClick={handleLogout}>Déconnexion</button>
          </>
        )}
      </div>
    </div>
  )
}
