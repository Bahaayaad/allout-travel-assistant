import { useState, useEffect, useRef, useCallback } from 'react'
import { sendMessage, openStream } from '../utils/api'

export function useChat() {
  const [convId] = useState(() => crypto.randomUUID())
  const [messages, setMessages] = useState([])
  const [isTyping, setIsTyping] = useState(false)
  const [connected, setConnected] = useState(false)
  const streamRef = useRef(null)

  useEffect(() => {
    const es = openStream(convId, (data) => {
      if (data.type === 'connected') {
        setConnected(true)
      } else if (data.type === 'typing') {
        setIsTyping(true)
      } else if (data.type === 'message') {
        setIsTyping(false)
        setMessages(prev => [...prev, {
          id: crypto.randomUUID(),
          role: data.role || 'assistant',
          content: data.content,
          escalation_id: data.escalation_id || null,
          ts: new Date()
        }])
      }
    })

    streamRef.current = es
    return () => es.close()
  }, [convId])

  const send = useCallback(async (text) => {
    if (!text.trim()) return

    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      ts: new Date()
    }])

    try {
      await sendMessage(convId, text)
    } catch (err) {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'system',
        content: 'Connection error. Please try again.',
        ts: new Date()
      }])
    }
  }, [convId])

  return { convId, messages, isTyping, connected, send }
}
