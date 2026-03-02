import { useState } from 'react'
import { supervisorReply } from '../utils/api'
import '../styles/chat.css'

export default function SupervisorPanel({ convId, messages }) {
  const [open, setOpen] = useState(false)
  const [escId, setEscId] = useState('')
  const [reply, setReply] = useState('')
  const [sending, setSending] = useState(false)

  const escRefs = [...new Set(
    messages
      .map(m => m.content?.match(/ESC-[A-Z0-9]+/)?.[0])
      .filter(Boolean)
  )]

  const send = async () => {
    if (!escId || !reply.trim()) return
    setSending(true)
    try {
      await supervisorReply(escId, convId, reply)
      setReply('')
      setEscId('')
    } catch (e) {
      console.error(e)
    }
    setSending(false)
  }

  return (
    <div style={{ position: 'fixed', bottom: 80, right: 20, zIndex: 1000 }}>
      <button
        className={`sup-trigger ${escRefs.length ? 'has-pending' : ''}`}
        onClick={() => setOpen(o => !o)}
        title="Supervisor panel"
      >
        👔
        {escRefs.length > 0 && (
          <span className="sup-badge">{escRefs.length}</span>
        )}
      </button>

      {open && (
        <div className="sup-panel">
          <h3>Supervisor Panel</h3>
          <p className="sub">Reply to customer escalations</p>

          {escRefs.length === 0 ? (
            <div className="sup-empty">No pending escalations</div>
          ) : (
            <>
              <select value={escId} onChange={e => setEscId(e.target.value)}>
                <option value="">Select escalation...</option>
                {escRefs.map(id => <option key={id} value={id}>{id}</option>)}
              </select>

              <textarea
                rows={4}
                value={reply}
                onChange={e => setReply(e.target.value)}
                placeholder="Type your response..."
              />

              <button
                className="send"
                onClick={send}
                disabled={!escId || !reply.trim() || sending}
              >
                {sending ? 'Sending...' : 'Send reply to customer'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
