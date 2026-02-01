import React, { useEffect, useState } from "react"

const App = () => {
  const [status, setStatus] = useState("idle")
  const [detail, setDetail] = useState("")
  const apiBase =
    import.meta.env.VITE_NEWS_APP_API_URL || "http://127.0.0.1:8001"

  const testHealth = async () => {
    try {
      setStatus("loading")
      setDetail("")
      const response = await fetch(`${apiBase}/health`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      setStatus("ok")
      setDetail(JSON.stringify(data))
    } catch (error) {
      setStatus("error")
      setDetail(error?.message || "Unknown error")
    }
  }

  useEffect(() => {
    testHealth()
  }, [])

  return (
    <div className="app">
      <div className="content">
        <div>hellow world</div>
        <div style={{ fontSize: 16, fontWeight: 400, marginTop: 12 }}>
          Backend health: {status}
        </div>
        {detail ? (
          <div
            style={{
              fontSize: 12,
              marginTop: 8,
              maxWidth: 600,
              wordBreak: "break-word",
            }}
          >
            {detail}
          </div>
        ) : null}
        <button
          type="button"
          onClick={testHealth}
          style={{ marginTop: 12, padding: "6px 10px" }}
        >
          Test API
        </button>
      </div>
    </div>
  )
}

export default App
