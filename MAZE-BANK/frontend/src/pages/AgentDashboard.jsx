import { useEffect, useState } from 'react'
import { api } from '../api.js'

const money = (n) => Number(n).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
const when = (d) => (d ? new Date(d).toLocaleString('fr-FR') : '—')
const TYPE_LABEL = { deposit: 'Dépôt', withdrawal: 'Retrait', transfer: 'Virement' }

export default function AgentDashboard() {
  const [pending, setPending] = useState([])
  const [clients, setClients] = useState([])
  const [selectedClient, setSelectedClient] = useState('')
  const [clientAccounts, setClientAccounts] = useState([])
  const [msg, setMsg] = useState(null)
  const [busyId, setBusyId] = useState(null)

  async function loadPending() {
    try {
      setPending(await api.pending())
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  async function loadClients() {
    try {
      setClients(await api.clients())
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  useEffect(() => { loadPending(); loadClients() }, [])

  async function decide(id, action) {
    setMsg(null)
    setBusyId(id)
    try {
      if (action === 'approve') await api.approve(id)
      else await api.reject(id)
      setMsg({ type: 'ok', text: `Opération #${id} ${action === 'approve' ? 'approuvée' : 'rejetée'}.` })
      loadPending()
      if (selectedClient) viewClient(selectedClient)
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    } finally {
      setBusyId(null)
    }
  }

  async function viewClient(id) {
    setSelectedClient(id)
    if (!id) { setClientAccounts([]); return }
    try {
      setClientAccounts(await api.clientAccounts(id))
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  async function removeClientAccount(account) {
    setMsg(null)
    if (!window.confirm(`Supprimer définitivement le compte ${account.number} de ce client ?`)) return
    try {
      await api.deleteAccount(account.id)
      setMsg({ type: 'ok', text: `Compte ${account.number} supprimé.` })
      viewClient(selectedClient)
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  async function renameClientAccount(account) {
    setMsg(null)
    const name = window.prompt('Nouveau nom du compte :', account.label)
    if (name === null) return
    const trimmed = name.trim()
    if (!trimmed) return
    try {
      await api.updateAccount(account.id, { label: trimmed })
      setMsg({ type: 'ok', text: `Compte ${account.number} renommé.` })
      viewClient(selectedClient)
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  return (
    <div className="page">
      <h1>Espace agent</h1>
      <div className="sub">Validez les opérations en attente et consultez les comptes clients.</div>

      {msg && <div className={`alert ${msg.type === 'ok' ? 'ok' : 'err'}`}>{msg.text}</div>}

      <div className="section-title">Opérations à valider ({pending.length})</div>
      {pending.length === 0 ? (
        <div className="card"><span className="muted">Aucune opération en attente.</span></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Date</th><th>Client</th><th>Type</th><th>Compte</th><th>Montant</th><th>Destinataire</th><th></th></tr>
            </thead>
            <tbody>
              {pending.map((o) => (
                <tr key={o.id}>
                  <td>{when(o.created_at)}</td>
                  <td>{o.created_by || `#${o.owner_id}`}</td>
                  <td>{TYPE_LABEL[o.type] || o.type}</td>
                  <td><span className="account-card"><span className="iban">{o.account_number}</span></span></td>
                  <td>{money(o.amount)}</td>
                  <td>{o.target_number ? `${o.target_number} (${o.target_owner_name || ''})` : '—'}</td>
                  <td>
                    <div className="row" style={{ flexWrap: 'nowrap' }}>
                      <button className="btn sm" disabled={busyId === o.id} onClick={() => decide(o.id, 'approve')}>Valider</button>
                      <button className="btn sm danger" disabled={busyId === o.id} onClick={() => decide(o.id, 'reject')}>Rejeter</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="section-title">Consulter les comptes d'un client</div>
      <div className="card">
        <div className="field" style={{ maxWidth: 380 }}>
          <label>Client</label>
          <select value={selectedClient} onChange={(e) => viewClient(e.target.value)}>
            <option value="">— Sélectionner un client —</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.full_name} ({c.email})</option>
            ))}
          </select>
        </div>

        {selectedClient && (
          clientAccounts.length === 0 ? (
            <span className="muted">Ce client n'a aucun compte.</span>
          ) : (
            <div className="table-wrap" style={{ marginTop: 8 }}>
              <table>
                <thead>
                  <tr><th>IBAN</th><th>Libellé</th><th>Solde actuel</th><th>Dernière opération</th><th></th></tr>
                </thead>
                <tbody>
                  {clientAccounts.map((a) => (
                    <tr key={a.id}>
                      <td className="iban">{a.number}</td>
                      <td>{a.label}</td>
                      <td><strong>{money(a.balance)}</strong></td>
                      <td>{when(a.last_operation_at)}</td>
                      <td>
                        <div className="row" style={{ flexWrap: 'nowrap' }}>
                          <button className="btn sm outline" onClick={() => renameClientAccount(a)}>Renommer</button>
                          <button className="btn sm danger" onClick={() => removeClientAccount(a)}>Supprimer</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </div>
  )
}
