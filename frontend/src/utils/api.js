const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API POST ${path} → ${res.status}`)
  return res.json()
}

export const api = {
  health:      () => get('/health'),
  equipment:   () => get('/equipment/'),
  alerts:      (limit = 20) => get(`/alerts/?limit=${limit}`),
  predict:     (payload) => post('/predict/', payload),
  modelInfo:   () => get('/predict/model-info'),
  replaceEquipment: (id) => post(`/equipment/${id}/replace`, {}),
}
