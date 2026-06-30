import { useEffect, useState } from 'react'
import { api } from '../api.js'

const money = (n) => Number(n).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
const when = (d) => (d ? new Date(d).toLocaleString('fr-FR') : '—')

const TYPE_LABEL = { deposit: 'Dépôt', withdrawal: 'Retrait', transfer: 'Virement' }
const STATUS_LABEL = { pending: 'En attente', approved: 'Validé', rejected: 'Refusé' }

export default function ClientDashboard() {
  const [accounts, setAccounts] = useState([])
  const [operations, setOperations] = useState([])
  const [msg, setMsg] = useState(null)

  // formulaire d'opération
  const [accountId, setAccountId] = useState('')
  const [type, setType] = useState('deposit')
  const [amount, setAmount] = useState('')
  const [targetNumber, setTargetNumber] = useState('')
  const [busy, setBusy] = useState(false)

  // édition du nom d'un compte
  const [editingId, setEditingId] = useState(null)
  const [editValue, setEditValue] = useState('')

  async function load() {
    try {
      const [acc, ops] = await Promise.all([api.myAccounts(), api.myOperations()])
      setAccounts(acc)
      setOperations(ops)
      setAccountId((cur) => {
        if (acc.length === 0) return ''
        if (cur && acc.some((a) => String(a.id) === String(cur))) return cur
        return String(acc[0].id)
      })
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  useEffect(() => { load() }, [])

  async function createAccount() {
    setMsg(null)
    try {
      await api.createAccount({ label: 'Compte courant' })
      setMsg({ type: 'ok', text: 'Nouveau compte ouvert.' })
      load()
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  async function removeAccount(account) {
    setMsg(null)
    if (!window.confirm(`Supprimer définitivement le compte ${account.number} ?`)) return
    try {
      await api.deleteAccount(account.id)
      setMsg({ type: 'ok', text: `Compte ${account.number} supprimé.` })
      load()
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  function startEdit(account) {
    setMsg(null)
    setEditingId(account.id)
    setEditValue(account.label)
  }

  function cancelEdit() {
    setEditingId(null)
    setEditValue('')
  }

  async function saveEdit(account) {
    const name = editValue.trim()
    if (!name) return
    try {
      await api.updateAccount(account.id, { label: name })
      setEditingId(null)
      setEditValue('')
      setMsg({ type: 'ok', text: 'Nom du compte mis à jour.' })
      load()
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  async function submitOperation(e) {
    e.preventDefault()
    setMsg(null)
    setBusy(true)
    try {
      const payload = { account_id: Number(accountId), type, amount: Number(amount) }
      if (type === 'transfer') payload.target_number = targetNumber
      await api.createOperation(payload)
      setMsg({
        type: 'ok',
        text: type === 'deposit'
          ? 'Dépôt effectué et crédité immédiatement.'
          : 'Opération enregistrée — en attente de validation par un agent.',
      })
      setAmount(''); setTargetNumber('')
      load()
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <h1>Mes comptes</h1>
      <div className="sub">Consultez vos comptes et réalisez vos opérations.</div>

      {msg && <div className={`alert ${msg.type === 'ok' ? 'ok' : 'err'}`}>{msg.text}</div>}

      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="section-title" style={{ margin: 0 }}>Comptes détenus</div>
        <button className="btn outline sm" onClick={createAccount}>+ Ouvrir un compte</button>
      </div>

      {accounts.length === 0 ? (
        <div className="card" style={{ marginTop: 12 }}>
          <span className="muted">Aucun compte pour l'instant. Cliquez sur « Ouvrir un compte ».</span>
        </div>
      ) : (
        <div className="grid cols-3" style={{ marginTop: 12 }}>
          {accounts.map((a) => (
            <div key={a.id} className="card accent account-card">
              <div className="iban">{a.number}</div>
              {editingId === a.id ? (
                <div style={{ margin: '6px 0' }}>
                  <input
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') saveEdit(a); if (e.key === 'Escape') cancelEdit() }}
                    autoFocus
                  />
                  <div className="row" style={{ marginTop: 8 }}>
                    <button className="btn sm" onClick={() => saveEdit(a)}>Enregistrer</button>
                    <button className="btn ghost sm" onClick={cancelEdit}>Annuler</button>
                  </div>
                </div>
              ) : (
                <div className="label">{a.label}</div>
              )}
              <div className="balance">{money(a.balance)}</div>
              <div className="meta">Dernière opération : {when(a.last_operation_at)}</div>
              {editingId !== a.id && (
                <div className="row" style={{ marginTop: 12 }}>
                  <button className="btn outline sm" onClick={() => startEdit(a)}>Renommer</button>
                  <button className="btn danger sm" onClick={() => removeAccount(a)}>Supprimer</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="grid cols-2" style={{ marginTop: 24 }}>
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Nouvelle opération</div>
          <form onSubmit={submitOperation}>
            <div className="field">
              <label>Compte</label>
              <select value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>{a.label} — {a.number} ({money(a.balance)})</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Type d'opération</label>
              <select value={type} onChange={(e) => setType(e.target.value)}>
                <option value="deposit">Dépôt (immédiat)</option>
                <option value="withdrawal">Retrait (validation requise)</option>
                <option value="transfer">Virement (validation requise)</option>
              </select>
            </div>
            {type === 'transfer' && (
              <div className="field">
                <label>IBAN destinataire</label>
                <input value={targetNumber} onChange={(e) => setTargetNumber(e.target.value)} placeholder="FR76…" required />
              </div>
            )}
            <div className="field">
              <label>Montant (€)</label>
              <input type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="100.00" required />
            </div>
            <button className="btn block" disabled={busy || accounts.length === 0}>
              {busy ? 'Envoi…' : 'Valider l\'opération'}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Historique des opérations</div>
          {operations.length === 0 ? (
            <span className="muted">Aucune opération.</span>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Date</th><th>Type</th><th>Montant</th><th>Statut</th></tr>
                </thead>
                <tbody>
                  {operations.map((o) => (
                    <tr key={o.id}>
                      <td>{when(o.created_at)}</td>
                      <td>{TYPE_LABEL[o.type] || o.type}{o.type === 'transfer' && o.target_number ? ` → ${o.target_number}` : ''}</td>
                      <td>{money(o.amount)}</td>
                      <td><span className={`badge ${o.status}`}>{STATUS_LABEL[o.status] || o.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
