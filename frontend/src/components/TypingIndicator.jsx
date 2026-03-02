import '../styles/chat.css'

export default function TypingIndicator() {
  return (
    <div className="typing-row">
      <div className="avatar sm">✈️</div>
      <div className="typing-bubble">
        <div className="dot" />
        <div className="dot" />
        <div className="dot" />
      </div>
    </div>
  )
}
