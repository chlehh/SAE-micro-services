// Chaque micro-service est exposé sur son propre port (plus de passerelle).
// En local, le navigateur les joint directement sur localhost.
const HOST = window.location.hostname || 'localhost'

const BASE = {
  auth:       `http://${HOST}:8001`,
  account:    `http://${HOST}:8002`,
  operation:  `http://${HOST}:8003`,
  validation: `http://${HOST}:8004`,
  log:        `http://${HOST}:8005`,
}

export function getToken() {
  return localStorage.getItem('token')
}

async function request(base, path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && getToken()) headers['Authorization'] = `Bearer ${getToken()}`

  const res = await fetch(base + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) {
    throw new Error((data && data.detail) || `Erreur ${res.status}`)
  }
  return data
}

export const api = {
  // --- auth-service (8001) ---
  register: (d) => request(BASE.auth, '/register', { method: 'POST', body: d, auth: false }),
  login: (d) => request(BASE.auth, '/login', { method: 'POST', body: d, auth: false }),
  me: () => request(BASE.auth, '/me'),
  clients: () => request(BASE.auth, '/clients'),

  // --- account-service (8002) ---
  myAccounts: () => request(BASE.account, '/accounts'),
  createAccount: (d) => request(BASE.account, '/accounts', { method: 'POST', body: d }),
  updateAccount: (id, d) => request(BASE.account, `/accounts/${id}`, { method: 'PATCH', body: d }),
  deleteAccount: (id) => request(BASE.account, `/accounts/${id}`, { method: 'DELETE' }),
  clientAccounts: (id) => request(BASE.account, `/clients/${id}/accounts`),

  // --- operation-service (8003) ---
  myOperations: () => request(BASE.operation, '/operations/mine'),
  accountOperations: (id) => request(BASE.operation, `/operations/account/${id}`),
  createOperation: (d) => request(BASE.operation, '/operations', { method: 'POST', body: d }),

  // --- validation-service (8004) ---
  pending: () => request(BASE.validation, '/pending'),
  approve: (id) => request(BASE.validation, `/${id}/approve`, { method: 'POST' }),
  reject: (id) => request(BASE.validation, `/${id}/reject`, { method: 'POST' }),

  // --- log-service (8005) ---
  logs: (qs) => request(BASE.log, `/logs${qs ? `?${qs}` : ''}`),
  stats: () => request(BASE.log, '/stats'),
}
