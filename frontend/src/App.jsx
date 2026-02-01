import React, { useEffect, useState } from "react"
import HeadlineItem from "./components/HeadlineItem.jsx"

// Cache configuration
const CACHE_KEY = "moltbook_news_cache"
const CACHE_DURATION_MS = 24 * 60 * 60 * 1000 // 24 hours in milliseconds

const App = () => {
  const [status, setStatus] = useState("idle")
  const [detail, setDetail] = useState("")
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const apiBase =
    import.meta.env.VITE_NEWS_APP_API_URL || "http://127.0.0.1:8001"
  
  // Submolts to scrape for news
  const submolts = [
    "technology",
    "memes",
    "general",
    "ailabs",
    "showcase",
    "meta",
    "protocols",
    "security",
    "agents",
    "modelwars"
  ]

  const slugify = (value) =>
    value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")

  // Cache helper functions
  const getCache = () => {
    try {
      const cached = localStorage.getItem(CACHE_KEY)
      if (!cached) return null
      
      const { articles, timestamp } = JSON.parse(cached)
      const age = Date.now() - timestamp
      
      // Check if cache is still valid (less than 24 hours old)
      if (age < CACHE_DURATION_MS) {
        const hoursRemaining = Math.round((CACHE_DURATION_MS - age) / (60 * 60 * 1000))
        console.log(`Cache hit! ${hoursRemaining} hours until refresh.`)
        return articles
      }
      
      console.log("Cache expired, will fetch fresh data.")
      return null
    } catch (e) {
      console.warn("Failed to read cache:", e)
      return null
    }
  }

  const setCache = (articles) => {
    try {
      const cacheData = {
        articles,
        timestamp: Date.now()
      }
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
      console.log("Cache updated with", articles.length, "articles")
    } catch (e) {
      console.warn("Failed to write cache:", e)
    }
  }

  // Listen for cache updates from other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === CACHE_KEY && e.newValue) {
        try {
          const { articles: newArticles } = JSON.parse(e.newValue)
          if (newArticles && newArticles.length > 0) {
            console.log("Cache updated from another tab, syncing...")
            setArticles(newArticles)
            setLoading(false)
          }
        } catch (err) {
          console.warn("Failed to sync cache from other tab:", err)
        }
      }
    }

    window.addEventListener("storage", handleStorageChange)
    return () => window.removeEventListener("storage", handleStorageChange)
  }, [])

  // Parse the markdown response to extract JSON articles with their submolts
  const parseNewsResponse = (markdownResponse) => {
    const parsedArticles = []
    
    // Split by community sections to extract submolt for each article
    // Format: ## Community N: https://www.moltbook.com/m/SUBMOLT
    const communitySections = markdownResponse.split(/## Community \d+:/)
    
    for (let i = 1; i < communitySections.length; i++) {
      const section = communitySections[i]
      
      // Extract submolt from URL in section header
      const submoltMatch = section.match(/https:\/\/www\.moltbook\.com\/m\/(\w+)/)
      const submolt = submoltMatch ? submoltMatch[1] : submolts[i - 1] || "unknown"
      
      // Find JSON article in this section
      const jsonRegex = /\{[^{}]*"title"[^{}]*"summary"[^{}]*"content"[^{}]*\}/g
      const matches = section.match(jsonRegex)
      
      if (matches) {
        for (const match of matches) {
          try {
            const article = JSON.parse(match)
            if (article.title && article.summary && article.content) {
              parsedArticles.push({
                ...article,
                submolt,
                slug: slugify(article.title)
              })
            }
          } catch (e) {
            console.warn("Failed to parse article JSON:", e)
          }
        }
      }
    }
    
    return parsedArticles
  }

  // Fetch news from Moltbook via the supervisor agent
  const fetchMoltbookNews = async (forceRefresh = false) => {
    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cachedArticles = getCache()
      if (cachedArticles && cachedArticles.length > 0) {
        setArticles(cachedArticles)
        setLoading(false)
        return
      }
    }

    const urls = submolts.map(s => `https://www.moltbook.com/m/${s}`)
    
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`${apiBase}/agent/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: "Scrape and summarize", 
          urls 
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      const parsedArticles = parseNewsResponse(data.response)
      
      if (parsedArticles.length > 0) {
        setArticles(parsedArticles)
        setCache(parsedArticles) // Save to cache
      } else {
        // Fallback: if parsing failed, create a single article from the raw response
        const fallbackArticles = [{
          title: "Moltbook Community Update",
          summary: "Latest news from the Moltbook AI agent community",
          content: data.response,
          slug: "moltbook-community-update",
          submolt: "general"
        }]
        setArticles(fallbackArticles)
        setCache(fallbackArticles)
      }
    } catch (err) {
      console.error("Failed to fetch news:", err)
      setError(err.message)
      
      // Try to use stale cache if available
      try {
        const cached = localStorage.getItem(CACHE_KEY)
        if (cached) {
          const { articles: staleArticles } = JSON.parse(cached)
          if (staleArticles && staleArticles.length > 0) {
            setArticles(staleArticles)
            setError(`${err.message} (showing cached data)`)
          }
        }
      } catch (e) {
        // Ignore cache read errors
      }
    } finally {
      setLoading(false)
    }
  }

  // Force refresh (bypass cache)
  const handleForceRefresh = () => {
    fetchMoltbookNews(true)
  }

  // Computed article lists for layout - each section shows unique articles
  // Layout: Featured (1) | Left column (3) | Right column (2) | Extra row (4)
  const featuredArticle = articles[0] || null
  const leftArticles = articles.slice(1, 4)    // articles 1, 2, 3
  const rightArticles = articles.slice(4, 6)   // articles 4, 5
  const extraArticles = articles.slice(6, 10)  // articles 6, 7, 8, 9

  const openArticleInNewTab = (article) => {
    const url = `${window.location.origin}/article/${article.slug}`
    window.open(url, "_blank", "noopener,noreferrer")
  }
  
  const handleBackToList = () => {
    setSelectedArticle(null)
  }
  
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

  // Load news on mount
  useEffect(() => {
    testHealth()
    fetchMoltbookNews()
  }, [])

  // Handle article deep linking
  useEffect(() => {
    if (articles.length === 0) return
    
    const path = window.location.pathname
    if (path.startsWith("/article/")) {
      const slug = path.replace("/article/", "")
      const match = articles.find((article) => article.slug === slug)
      if (match) {
        setSelectedArticle(match)
      }
    }
  }, [articles])


  return (
    <div className="app">
      <div className={`content ${selectedArticle ? "article-page" : ""}`}>
        {selectedArticle ? (
          <div className="article-view">
            <div className="article-header">
              <div className="article-date">{todayLabel}</div>
              <div className="article-site-title">Agncity Times</div>
            </div>
            <hr className="article-divider" />
            <button
              type="button"
              className="back-button"
              onClick={handleBackToList}
            >
              ← Back
            </button>
            <div className="article-title">{selectedArticle.title}</div>
            <div className="article-summary">{selectedArticle.summary}</div>
            <div className="article-content">{selectedArticle.content}</div>
          </div>
        ) : (
          <>
            <div className="header">
              <div className="date-box">{todayLabel}</div>
              <div className="title">
                <img className="title-icon" src="/icon.png" alt="Agncity" />
                gncity Times
              </div>
              <div className="header-spacer" />
            </div>
            <div className="tagline">
              Your daily digest of AI agent chatter
            </div>
            <hr className="divider" />
            <nav className="nav">
              <span>technology</span>
              <span>memes</span>
              <span>ai labs</span>
              <span>model wars</span>
            </nav>
            
            {loading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Fetching news from Moltbook...</p>
                <p className="loading-detail">Scraping {submolts.length} communities</p>
              </div>
            ) : error ? (
              <div className="error-container">
                <p>Failed to load news: {error}</p>
                <button onClick={() => fetchMoltbookNews(true)}>Retry</button>
              </div>
            ) : (
              <>
                <div className="split-section">
                  <div className="split-left">
                    <div className="split-left-content">
                      {leftArticles.map((article, index) => (
                        <HeadlineItem
                          key={`left-${article.slug}-${index}`}
                          title={article.title}
                          summary={article.summary}
                          submolt={article.submolt}
                          onClick={() => openArticleInNewTab(article)}
                        />
                      ))}
                    </div>
                    <div className="split-line split-line-inner" />
                    <div className="main-headline">
                      <img
                        className="main-image"
                        src="https://upload.wikimedia.org/wikipedia/commons/3/34/Valkyrie-robot-3.jpg"
                        alt="Feature"
                      />
                      {featuredArticle ? (
                        <HeadlineItem
                          title={featuredArticle.title}
                          summary={featuredArticle.summary}
                          submolt={featuredArticle.submolt}
                          onClick={() => openArticleInNewTab(featuredArticle)}
                        />
                      ) : null}
                    </div>
                  </div>
                  <div className="split-line split-line-outer" />
                  <div className="split-right">
                    <img className="right-image" src="https://images.unsplash.com/photo-1694903110330-cc64b7e1d21d?q=80&w=2232&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"/>
                    
                    {rightArticles.map((article, index) => (
                      <HeadlineItem
                        key={`right-${article.slug}-${index}`}
                        title={article.title}
                        summary={article.summary}
                        submolt={article.submolt}
                        onClick={() => openArticleInNewTab(article)}
                      />
                    ))}
                  </div>
                </div>
                <div className="extra-articles">
                  {extraArticles.map((article, index) => (
                    <HeadlineItem
                      key={`extra-${article.slug}-${index}`}
                      title={article.title}
                      summary={article.summary}
                      submolt={article.submolt}
                      onClick={() => openArticleInNewTab(article)}
                    />
                  ))}
                </div>
              </>
            )}
            
            <footer className="footer">
              <a className="footer-link" href="/about">
                About Us
              </a>
              <button 
                className="refresh-button" 
                onClick={handleForceRefresh}
                disabled={loading}
              >
                🔄 Refresh News (every 24h)
              </button>
            </footer>
          </>
        )}
      </div>
    </div>
  )
}

export default App
