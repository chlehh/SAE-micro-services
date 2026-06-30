import { useEffect, useState } from 'react'
import { api } from '../api.js'

const when = (d) => (d ? new Date(d).toLocaleString('fr-FR') : '—')
const SERVICES = ['auth-service', 'account-service', 'operation-service', 'validation-service', 'log-service']
const LEVELS = ['INFO', 'WARNING', 'ERROR']

export default function Logs() {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [msg, setMsg] = useState(null)

  const [service, setService] = useState('')
  const [level, setLevel] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  async function loadStats() {
    try { setStats(await api.stats()) } catch (err) { setMsg({ type: 'err', text: err.message }) }
  }

  async function loadLogs() {
    setMsg(null)
    const params = new URLSearchParams()
    if (service) params.set('service', service)
    if (level) params.set('level', level)
    if (dateFrom) params.set('date_from', new Date(dateFrom).toISOString())
    if (dateTo) params.set('date_to', new Date(dateTo).toISOString())
    try {
      setLogs(await api.logs(params.toString()))
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  useEffect(() => { loadStats(); loadLogs() }, [])

  function reset() {
    setService(''); setLevel(''); setDateFrom(''); setDateTo('')
    setTimeout(loadLogs, 0)
  }

  return (
    <div className="page">
      <h1>Journaux d'activité</h1>
      <div className="sub">Logs collectés via NATS depuis tous les micro-services.</div>

      {msg && <div className={`alert ${msg.type === 'ok' ? 'ok' : 'err'}`}>{msg.text}</div>}

      {stats && (
        <div className="grid cols-3" style={{ marginBottom: 20 }}>
          <div className="metric"><div className="k">Total des logs</div><div className="v">{stats.total}</div></div>
          <div className="metric">
            <div className="k">Par niveau</div>
            <div className="v" style={{ fontSize: 15, fontWeight: 600 }}>
              {Object.entries(stats.par_niveau || {}).map(([k, v]) => `${k}: ${v}`).join('  ·  ') || '—'}
            </div>
          </div>
          <div className="metric">
            <div className="k">Services actifs</div>
            <div className="v">{Object.keys(stats.par_service || {}).length}</div>
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row">
          <div className="field" style={{ flex: 1, minWidth: 160 }}>
            <label>Service</label>
            <select value={service} onChange={(e) => setService(e.target.value)}>
              <option value="">Tous</option>
              {SERVICES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="field" style={{ flex: 1, minWidth: 140 }}>
            <label>Niveau</label>
            <select value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="">Tous</option>
              {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>Du</label>
            <input type="datetime-local" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>Au</label>
            <input type="datetime-local" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
        </div>
        <div className="row">
          <button className="btn" onClick={loadLogs}>Filtrer</button>
          <button className="btn ghost" onClick={reset}>Réinitialiser</button>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Horodatage</th><th>Service</th><th>Niveau</th><th>Action</th><th>Message</th></tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr><td colSpan={5}><span className="muted">Aucun log pour ces critères.</span></td></tr>
            ) : (
              logs.map((l) => (
                <tr key={l.id}>
                  <td>{when(l.event_time)}</td>
                  <td>{l.service}</td>
                  <td><span className={`badge ${l.level.toLowerCase()}`}>{l.level}</span></td>
                  <td>{l.action}</td>
                  <td>{l.message}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
