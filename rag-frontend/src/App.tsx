import React, { useState } from 'react'
import { MessageSquare, Upload, Activity, Send, Bot, User, Loader2, CheckCircle, XCircle } from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  contextCount?: number
}

interface UploadedFile {
  id: string
  name: string
  size: number
  status: 'uploading' | 'success' | 'error'
  chunks?: number
  error?: string
}

type Tab = 'chat' | 'upload' | 'status'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [systemStatus, setSystemStatus] = useState({
    overall: true,
    vectordb: true,
    llm: true,
    message: 'System operational'
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input.trim() }),
      })

      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.statusText}`)
      }

      const data = await response.json()
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        contextCount: data.context_count,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files
    if (!selectedFiles) return

    const newFiles: UploadedFile[] = Array.from(selectedFiles)
      .filter(file => file.type === 'application/pdf')
      .map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        status: 'uploading' as const,
      }))

    setFiles(prev => [...prev, ...newFiles])

    // Upload files
    newFiles.forEach(async (fileInfo) => {
      try {
        const file = selectedFiles[Array.from(selectedFiles).findIndex(f => f.name === fileInfo.name)]
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('http://localhost:8000/files/add_file', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`File upload failed: ${response.statusText}`)
        }

        const data = await response.json()
        
        setFiles(prev => prev.map(f => 
          f.id === fileInfo.id 
            ? { ...f, status: 'success', chunks: data.total_chunks }
            : f
        ))
      } catch (error) {
        setFiles(prev => prev.map(f => 
          f.id === fileInfo.id 
            ? { ...f, status: 'error', error: error instanceof Error ? error.message : 'Upload failed' }
            : f
        ))
      }
    })
  }

  const checkSystemStatus = async () => {
    try {
      const [health, filesHealth] = await Promise.all([
        fetch('http://localhost:8000/health').then(r => r.json()),
        fetch('http://localhost:8000/files/health').then(r => r.json())
      ])
      
      setSystemStatus({
        overall: filesHealth.overall,
        vectordb: filesHealth.vectordb,
        llm: filesHealth.llm,
        message: health.message
      })
    } catch (error) {
      console.error('Status check failed:', error)
      setSystemStatus({
        overall: false,
        vectordb: false,
        llm: false,
        message: 'Status check failed'
      })
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <Bot className="logo-icon" />
            <h1 className="logo-text">Agentic RAG System</h1>
          </div>
          <nav className="nav">
            {[
              { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
              { id: 'upload' as const, label: 'Upload', icon: Upload },
              { id: 'status' as const, label: 'Status', icon: Activity },
            ].map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`nav-button ${activeTab === tab.id ? 'active' : ''}`}
                >
                  <Icon size={16} />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {activeTab === 'chat' && (
          <div className="chat-container">
            {/* Messages */}
            <div className="messages">
              {messages.length === 0 && (
                <div className="empty-state">
                  <Bot className="empty-icon" />
                  <h3 className="empty-title">Welcome to your RAG Assistant!</h3>
                  <p className="empty-subtitle">Ask me anything about your uploaded documents.</p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message ${message.type}`}
                >
                  <div className={`message-avatar ${message.type}`}>
                    {message.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  
                  <div className="message-content">
                    <div className="message-text">{message.content}</div>
                    {message.contextCount !== undefined && message.contextCount > 0 && (
                      <div className="message-sources">
                        <span className="sources-badge">
                          {message.contextCount} sources
                        </span>
                      </div>
                    )}
                    <div className="message-meta">
                      {message.type === 'user' ? <User size={12} /> : <Bot size={12} />}
                      <span>{formatDate(message.timestamp)}</span>
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="message assistant">
                  <div className="message-avatar assistant">
                    <Bot size={16} />
                  </div>
                  <div className="message-content">
                    <div className="loading-message">
                      <Loader2 className="loading-spinner" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="input-container">
              <form onSubmit={handleSubmit} className="input-form">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  disabled={isLoading}
                  className="input-field"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="send-button"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>
        )}
        
        {activeTab === 'upload' && (
          <div className="upload-container">
            <div className="upload-content">
              <div className="upload-card">
                <h2 className="upload-title">
                  <Upload size={20} />
                  Upload Documents
                </h2>
                <div className="upload-area" onClick={() => document.getElementById('file-upload')?.click()}>
                  <Upload className="upload-icon" />
                  <p className="upload-text">Drop PDF files here</p>
                  <p className="upload-subtext">or click to select files</p>
                  <button className="upload-button">
                    Select Files
                  </button>
                </div>
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="file-input"
                  id="file-upload"
                />
              </div>

              {files.length > 0 && (
                <div className="upload-card">
                  <h3 className="upload-title">Uploaded Files</h3>
                  <div className="file-list">
                    {files.map((file) => (
                      <div key={file.id} className="file-item">
                        <div className="file-info">
                          <div className="file-icon">📄</div>
                          <div className="file-details">
                            <h4>{file.name}</h4>
                            <div className="file-meta">
                              <span>{formatFileSize(file.size)}</span>
                              <span>•</span>
                              <div className="file-status">
                                {file.status === 'uploading' && <Loader2 className="status-icon loading" />}
                                {file.status === 'success' && <CheckCircle className="status-icon success" />}
                                {file.status === 'error' && <XCircle className="status-icon error" />}
                                <span>
                                  {file.status === 'uploading' && 'Uploading...'}
                                  {file.status === 'success' && `Uploaded (${file.chunks} chunks)`}
                                  {file.status === 'error' && (file.error || 'Upload failed')}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        {file.status === 'success' && file.chunks && (
                          <div className="file-badge">
                            {file.chunks} chunks
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'status' && (
          <div className="status-container">
            <div className="status-content">
              <div className="status-card">
                <h2 className="status-title">
                  <Activity size={20} />
                  System Status
                </h2>
                <div className="status-list">
                  <div className="status-item">
                    <span className="status-label">Overall System</span>
                    <div className="status-indicator">
                      {systemStatus.overall ? (
                        <CheckCircle className="status-icon success" />
                      ) : (
                        <XCircle className="status-icon error" />
                      )}
                      <span className={`status-badge ${systemStatus.overall ? 'healthy' : 'unhealthy'}`}>
                        {systemStatus.overall ? 'Healthy' : 'Unhealthy'}
                      </span>
                    </div>
                  </div>
                  <div className="status-item">
                    <span className="status-label">Vector Database</span>
                    <div className="status-indicator">
                      {systemStatus.vectordb ? (
                        <CheckCircle className="status-icon success" />
                      ) : (
                        <XCircle className="status-icon error" />
                      )}
                      <span className={`status-badge ${systemStatus.vectordb ? 'healthy' : 'unhealthy'}`}>
                        {systemStatus.vectordb ? 'Healthy' : 'Unhealthy'}
                      </span>
                    </div>
                  </div>
                  <div className="status-item">
                    <span className="status-label">LLM Service</span>
                    <div className="status-indicator">
                      {systemStatus.llm ? (
                        <CheckCircle className="status-icon success" />
                      ) : (
                        <XCircle className="status-icon error" />
                      )}
                      <span className={`status-badge ${systemStatus.llm ? 'healthy' : 'unhealthy'}`}>
                        {systemStatus.llm ? 'Healthy' : 'Unhealthy'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="status-message">
                  {systemStatus.message}
                </div>
                <button
                  onClick={checkSystemStatus}
                  className="refresh-button"
                >
                  Refresh Status
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App