const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function sendMessage(convId, message) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: convId, message })
  })
  if (!res.ok) throw new Error('Failed to send')
  return res.json()
}

export function openStream(convId, onEvent, onError) {
  const es = new EventSource(`${BASE}/api/stream/${convId}`)
  es.onmessage = (e) => {
    try { onEvent(JSON.parse(e.data)) } catch {}
  }
  es.onerror = onError || (() => {})
  return es
}

export async function supervisorReply(escId, convId, response) {
  return fetch(`${BASE}/api/supervisor/reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ escalation_id: escId, conversation_id: convId, response })
  }).then(r => r.json())
}
