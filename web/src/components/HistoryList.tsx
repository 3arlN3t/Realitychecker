import React, { useEffect, useState } from 'react'

type HistoryItem = {
  id: number
  source: 'web_upload' | 'whatsapp'
  score: number | null
  verdict: string | null
  created_at: string
  file_name: string | null
  message_preview: string | null
  phone_last4: string | null
  correlation_id: string | null
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

function SourceBadge({ source }: { source: HistoryItem['source'] }) {
  const label = source === 'web_upload' ? 'web' : 'whatsapp'
  const color = source === 'web_upload' ? '#0ea5e9' : '#22c55e'
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 6px',
      borderRadius: 6,
      fontSize: 12,
      color: 'white',
      backgroundColor: color,
      textTransform: 'uppercase',
    }}>{label}</span>
  )
}

export default function HistoryList() {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('/api/history?source=all&limit=50')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data: HistoryItem[] = await res.json()
        if (!cancelled) setItems(data)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <div>Loading…</div>
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>

  return (
    <div>
      <h3>Recent Analyses &amp; History</h3>
      {items.length === 0 && <div>No history yet.</div>}
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {items.map(item => (
          <li key={item.id} style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
            padding: '10px 0',
            borderBottom: '1px solid #eee'
          }}>
            <div style={{ width: 80 }}><SourceBadge source={item.source} /></div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>
                {item.source === 'web_upload' ? (item.file_name || '(no filename)') : (item.message_preview || '(no preview)')}
              </div>
              <div style={{ color: '#555', fontSize: 13 }}>
                {item.verdict || ''}{item.verdict && (item.score !== null) ? ' · ' : ''}{item.score !== null ? `score ${item.score.toFixed(2)}` : ''}
              </div>
              <div style={{ color: '#777', fontSize: 12 }}>
                {formatDate(item.created_at)}{item.phone_last4 ? ` · ****${item.phone_last4}` : ''}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

