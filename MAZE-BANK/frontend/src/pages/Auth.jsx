import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Logo from '../components/Logo.jsx'
import { api } from '../api.js'
import { useAuth } from '../auth.jsx'

export default function Auth() {
  const [tab, setTab] = useState('login')
  const { login } = useAuth()
  const navigate = useNavigate()

  // état connexion
  const [lEmail, setLEmail] = useState('')
  const [lPass, setLPass] = useState('')
  const [lMsg, setLMsg] = useState(null)

  // état inscription
  const [rName, setRName] = useState('')
  const [rEmail, setREmail] = useState('')
  const [rRole, setRRole] = useState('client')
  const [rPass, setRPass] = useState('')
  const [rPass2, setRPass2] = useState('')
  const [rMsg, setRMsg] = useState(null)

  const [busy, setBusy] = useState(false)

  async function handleLogin(e) {
    e.preventDefault()
    setLMsg(null)
    setBusy(true)
    try {
      const r = await api.login({ email: lEmail, password: lPass })
      login(r.access_token, { user_id: r.user_id, full_name: r.full_name, role: r.role })
      navigate(r.role === 'agent' ? '/agent' : '/client')
    } catch (err) {
      setLMsg({ type: 'err', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setRMsg(null)
    if (rPass !== rPass2) {
      setRMsg({ type: 'err', text: 'Les mots de passe ne correspondent pas.' })
      return
    }
    setBusy(true)
    try {
      await api.register({ full_name: rName, email: rEmail, password: rPass, role: rRole })
      setRMsg({ type: 'ok', text: 'Compte créé ! Vous pouvez vous connecter.' })
      setRName(''); setREmail(''); setRPass(''); setRPass2('')
      setLEmail(rEmail)
      setTimeout(() => setTab('login'), 900)
    } catch (err) {
      setRMsg({ type: 'err', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="topbar" />
        <div className="head"><Logo size={28} /></div>
        <div className="baseline">BANQUE EN LIGNE</div>

        <div className="tabs">
          <div className={`tab ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>Se connecter</div>
          <div className={`tab ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>Créer un compte</div>
        </div>

        {tab === 'login' ? (
          <form className="auth-form" onSubmit={handleLogin}>
            {lMsg && <div className={`alert ${lMsg.type === 'ok' ? 'ok' : 'err'}`}>{lMsg.text}</div>}
            <div className="field">
              <label>Adresse e-mail</label>
              <input type="email" value={lEmail} onChange={(e) => setLEmail(e.target.value)} placeholder="prenom.nom@mazebank.fr" required />
            </div>
            <div className="field">
              <label>Mot de passe</label>
              <input type="password" value={lPass} onChange={(e) => setLPass(e.target.value)} placeholder="••••••••" required />
            </div>
            <button className="btn block" disabled={busy}>{busy ? 'Connexion…' : 'Se connecter'}</button>
            <div className="hint">Accès clients &amp; agents bancaires</div>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegister}>
            {rMsg && <div className={`alert ${rMsg.type === 'ok' ? 'ok' : 'err'}`}>{rMsg.text}</div>}
            <div className="field">
              <label>Nom complet</label>
              <input type="text" value={rName} onChange={(e) => setRName(e.target.value)} placeholder="Jean Dupont" required />
            </div>
            <div className="field">
              <label>Adresse e-mail</label>
              <input type="email" value={rEmail} onChange={(e) => setREmail(e.target.value)} placeholder="prenom.nom@mazebank.fr" required />
            </div>
            <div className="field">
              <label>Type de compte</label>
              <select value={rRole} onChange={(e) => setRRole(e.target.value)}>
                <option value="client">Client</option>
                <option value="agent">Agent bancaire</option>
              </select>
            </div>
            <div className="row">
              <div className="field" style={{ flex: 1 }}>
                <label>Mot de passe</label>
                <input type="password" value={rPass} onChange={(e) => setRPass(e.target.value)} placeholder="6 caractères min." required />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Confirmer</label>
                <input type="password" value={rPass2} onChange={(e) => setRPass2(e.target.value)} placeholder="Confirmer" required />
              </div>
            </div>
            <button className="btn block" disabled={busy}>{busy ? 'Création…' : 'Créer mon compte'}</button>
            <div className="hint">Vos retraits et virements seront validés par un agent.</div>
          </form>
        )}
      </div>
    </div>
  )
}
