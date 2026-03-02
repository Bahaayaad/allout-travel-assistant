import { useState, useRef } from 'react'
import '../styles/chat.css'

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  const handleSend = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const onInput = (e) => {
    setValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  return (
    <div className="input-area">
      <textarea
        ref={ref}
        rows={1}
        value={value}
        onChange={onInput}
        onKeyDown={onKeyDown}
        placeholder="Type a message"
        disabled={disabled}
      />
      <button
        className={"send-btn " + (value.trim() ? 'active' : 'inactive')}
        onClick={handleSend}
        disabled={!value.trim() || disabled}
      >
        {value.trim() ? '>' : 'mic'}
      </button>
    </div>
  )
}
