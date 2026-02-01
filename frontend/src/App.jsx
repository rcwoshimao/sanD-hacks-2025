import React, { useEffect, useState } from "react"

const App = () => {
  const [status, setStatus] = useState("idle")
  const [detail, setDetail] = useState("")
  const apiBase =
    import.meta.env.VITE_NEWS_APP_API_URL || "http://127.0.0.1:8001"
  const todayLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })

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
        <div className="header">
          <div className="date-box">{todayLabel}</div>
          <div className="title">Agncity Times</div>
          <div className="header-spacer" />
        </div>
        <hr className="divider" />
        <nav className="nav">
          <span>technology</span>
          <span>memes</span>
          <span>ai labs</span>
          <span>model wars</span>
        </nav>
        
        <div className="split-section">
          <div className="split-left">
            <div className="split-left-content">
              <div className="headline-item">
                <div className="headline-title">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit
                </div>
                
                <div className="headline-summary">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </div>
                <div className="headline-divider" />
              </div>
              <div className="headline-item">
                <div className="headline-title">
                  Sed do eiusmod tempor incididunt ut labore et dolore
                </div>
                
                <div className="headline-summary">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </div>
                <div className="headline-divider" />
              </div>
              <div className="headline-item">
                <div className="headline-title">
                  Ut enim ad minim veniam, quis nostrud exercitation
                </div>
                
                <div className="headline-summary">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </div>
                <div className="headline-divider" />
              </div>
            </div>
            <div className="split-line split-line-inner" />
            <div className="main-headline">
              <img
                className="main-image"
                src="https://images.unsplash.com/photo-1768755457768-f4d561ab158e?q=80&w=2067&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
                alt="Feature"
              />
              <div className="headline-title">
                  Ut enim ad minim veniam, quis nostrud exercitation
                </div>
                 
                <div className="headline-summary">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </div>
                <div className="headline-divider" />
            </div>
          </div>
          <div className="split-line split-line-outer" />
          <div className="split-right">
                <img className="right-image" src="https://images.unsplash.com/photo-1496318447583-f524534e9ce1?q=80&w=2134&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"/>
            
            <div className="headline-title">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit
            </div>
            <div className="headline-summary">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            </div>
          </div>
        </div>








        
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
