import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import '../styles/chat.css'

// matches both plain https://...jpg URLs and markdown image syntax ![alt](url)
const PLAIN_IMG = /https?:\/\/(images\.unsplash\.com\/[^\s"')]+|[^\s"']+\.(?:jpg|jpeg|png|webp|gif))(?:\?[^\s"')\]]*)?/gi
const MD_IMG = /!\[[^\]]*\]\((https?:\/\/[^)]+)\)/g

function extractImages(text) {
  const urls = new Set()
  for (const m of text.matchAll(MD_IMG)) urls.add(m[1])
  for (const m of text.matchAll(PLAIN_IMG)) urls.add(m[0])
  return [...urls]
}

function stripImageUrls(text) {
  return text
    .replace(MD_IMG, '')
    .replace(PLAIN_IMG, '')
    .trim()
}

function ActivityImage({ url }) {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  if (error) return null

  return (
    <div className="activity-img-wrap">
      {!loaded && <div className="activity-img-placeholder">Loading...</div>}
      <img
        src={url}
        alt="Activity"
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        style={{ display: loaded ? 'block' : 'none' }}
      />
    </div>
  )
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', hour12: true
  })
}

export default function MessageBubble({ message }) {
  const { role, content, ts } = message

  if (role === 'system') {
    return (
      <div className="bubble-row system">
        <span>{content}</span>
      </div>
    )
  }

  const images = role !== 'user' ? extractImages(content) : []
  const text = role !== 'user' ? stripImageUrls(content) : content

  return (
    <div className={`bubble-row ${role}`}>
      {(role === 'assistant' || role === 'supervisor') && (
        <div className="avatar sm">
          {role === 'supervisor' ? '👔' : '✈️'}
        </div>
      )}

      <div className="bubble">
        {role === 'supervisor' && (
          <div className="supervisor-label">Supervisor</div>
        )}
        <div className="bubble-inner">
          <div className="bubble-text">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>

          {images.map((url, i) => <ActivityImage key={i} url={url} />)}

          <div className="bubble-meta">
            <span className="bubble-time">{formatTime(ts)}</span>
            {role === 'user' && <span className="bubble-ticks">✓✓</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
