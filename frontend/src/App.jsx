import { useEffect, useRef } from 'react'
import { useChat } from './hooks/useChat'
import MessageBubble from './components/MessageBubble'
import TypingIndicator from './components/TypingIndicator'
import ChatInput from './components/ChatInput'
import SupervisorPanel from './components/SupervisorPanel'
import './styles/global.css'
import './styles/chat.css'

function fmtDate(date) {
  const d = new Date(date)
  if (d.toDateString() === new Date().toDateString()) return 'Today'
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function App() {
  const { convId, messages, isTyping, connected, send } = useChat()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  // inject date separators
  const items = []
  let lastDate = null
  for (const msg of messages) {
    const d = fmtDate(msg.ts)
    if (d !== lastDate) {
      items.push({ type: 'date', id: d + msg.id, value: d })
      lastDate = d
    }
    items.push({ type: 'msg', id: msg.id, value: msg })
  }

  const lastMsg = messages[messages.length - 1]

  return (
    <div className="app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="avatar">✈️</div>
          <div>
            <h1>Allout Travel</h1>
            <p>Dubai Activity Booking</p>
          </div>
        </div>

        <div className="sidebar-conversation">
          <div className="avatar lg">🤖</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 500, fontSize: 15 }}>AI Travel Assistant</div>
            <div className="preview">
              {lastMsg ? lastMsg.content.slice(0, 45) + '...' : 'Start a conversation'}
            </div>
          </div>
        </div>

        <div className="sidebar-footer">
          {convId.slice(0, 8)}...
          <br />
          <span className={`status-dot ${connected ? 'connected' : ''}`}>
            ● {connected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
      </div>

      <div className="chat-area">
        <div className="chat-bg" />

        <div className="chat-header">
          <div className="avatar">🤖</div>
          <div>
            <div className="name">AI Travel Assistant</div>
            <div className={`sub ${isTyping ? 'typing' : ''}`}>
              {isTyping ? 'typing...' : connected ? 'online' : 'connecting...'}
            </div>
          </div>
          <div className="chat-header-actions">
            <span title="Search">🔍</span>
            <span title="More">⋮</span>
          </div>
        </div>

        <div className="messages-area">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="emoji">🏙️</div>
              <h2>Welcome to Allout Travel</h2>
              <p>Discover and book the best Dubai experiences</p>
              <div className="welcome-chips">
                {['🏜️ Desert Safari', '🗼 Burj Khalifa', '⛵ Marina Cruise', '❄️ Ski Dubai'].map(tag => (
                  <button key={tag} className="chip" onClick={() => send(`Tell me about ${tag.slice(3)}`)}>
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {items.map(item =>
            item.type === 'date'
              ? (
                <div key={item.id} className="date-separator">
                  <span>{item.value}</span>
                </div>
              )
              : <MessageBubble key={item.id} message={item.value} />
          )}

          {isTyping && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <ChatInput onSend={send} disabled={!connected} />
      </div>

      <SupervisorPanel convId={convId} messages={messages} />
    </div>
  )
}
