import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  MessageSquare, 
  Upload, 
  Activity, 
  Send, 
  Bot, 
  User, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Sun, 
  Moon,
  FileText,
  Trash2,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Zap,
  Database,
  Brain
} from 'lucide-react';
import './index.css';

// Types
type Tab = 'chat' | 'upload' | 'status';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  contextCount?: number;
  isTyping?: boolean;
}

interface UploadedFile {
  id: string;
  backendFileId: string | null;
  name: string;
  size: number;
  status: 'uploading' | 'success' | 'error';
  chunks?: number;
  error?: string;
  uploadProgress?: number;
}

interface HealthStatus {
  vectordb: boolean;
  llm: boolean;
  overall: boolean;
  message: string;
}

// API functions
const API_BASE = 'http://localhost:8000';

const fetchBackend = async (endpoint: string, options?: RequestInit) => {
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || response.statusText);
  }
  return response.json();
};

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

// Medical sample questions for empty state
const sampleQuestions = [
  "What are the clinical manifestations of acute myocardial infarction?",
  "Explain the pharmacokinetics and contraindications of ACE inhibitors",
  "What are the SIRS criteria and sepsis diagnostic protocols?",
  "Describe the staging and management of chronic kidney disease",
  "What are the absolute contraindications for MRI contrast agents?",
  "Explain the pathophysiology and complications of Type 2 diabetes mellitus",
  "What are the common adverse effects of chemotherapy regimens?",
  "Describe the emergency management protocol for anaphylactic shock"
];

const App: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme');
    return (saved as 'light' | 'dark') || 'light';
  });
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      } catch {
        return [];
      }
    }
    return [];
  });
  const [input, setInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [dragActive, setDragActive] = useState(false);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Effects
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Utility functions
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const clearChatHistory = () => {
    if (window.confirm('Are you sure you want to clear all chat history?')) {
      setMessages([]);
      localStorage.removeItem('chatHistory');
    }
  };

  // API functions
  const checkSystemStatus = async () => {
    try {
      const [healthResponse, filesHealthResponse] = await Promise.all([
        fetchBackend('/health'),
        fetchBackend('/files/health')
      ]);
      
      setHealth({
        overall: filesHealthResponse.overall,
        vectordb: filesHealthResponse.vectordb,
        llm: filesHealthResponse.llm,
        message: healthResponse.message
      });
    } catch (error) {
      console.error('Status check failed:', error);
      setHealth({ 
        vectordb: false, 
        llm: false, 
        overall: false, 
        message: `Status check failed: ${error instanceof Error ? error.message : String(error)}` 
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isChatLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsChatLoading(true);

    // Add typing indicator
    const typingMessage: Message = {
      id: 'typing',
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isTyping: true,
    };
    setMessages(prev => [...prev, typingMessage]);

    try {
      const data = await fetchBackend('/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input.trim() }),
      });
      
      // Remove typing indicator and add real response
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== 'typing');
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.answer,
          timestamp: new Date(),
          contextCount: data.context_count,
        };
        return [...filtered, assistantMessage];
      });
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== 'typing');
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : String(error)}. Please try again.`,
          timestamp: new Date(),
        };
        return [...filtered, errorMessage];
      });
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleSampleQuestion = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  const previewCSV = async (file: File): Promise<boolean> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const info = await fetchBackend('/files/csv_info', {
        method: 'POST',
        body: formData,
      });
      
      if (info.warning) {
        const message = `${info.warning}\n\nFile: ${file.name}\nEstimated Documents: ${info.estimated_documents}\nEstimated Time: ${info.estimated_time_minutes} minutes\n\nDo you want to continue?`;
        return window.confirm(message);
      }
      
      return true;
    } catch (error) {
      console.error('CSV preview error:', error);
      // If preview fails, ask user if they want to proceed anyway
      return window.confirm(`Unable to preview CSV file. Upload anyway?`);
    }
  };

  const handleFileUpload = async (files: FileList | null, existingFileId: string | null = null) => {
    if (!files || files.length === 0) return;

    Array.from(files).forEach(async (file) => {
      const tempId = existingFileId || Math.random().toString(36).substr(2, 9);
      const isCSV = file.name.toLowerCase().endsWith('.csv');
      
      // Preview CSV files before uploading
      if (isCSV && !existingFileId) {
        const shouldProceed = await previewCSV(file);
        if (!shouldProceed) {
          return; // User cancelled
        }
      }
      
      const newFile: UploadedFile = {
        id: tempId,
        backendFileId: existingFileId,
        name: file.name,
        size: file.size,
        status: 'uploading',
        chunks: 0,
        error: undefined,
        uploadProgress: 0,
      };

      if (!existingFileId) {
        setUploadedFiles(prev => [...prev, newFile]);
      } else {
        setUploadedFiles(prev => prev.map(f => f.id === tempId ? { ...f, ...newFile } : f));
      }

      try {
        const formData = new FormData();
        formData.append('file', file);

        // Show progress animation for CSV files (they take longer)
        let progressInterval: ReturnType<typeof setInterval> | null = null;
        if (isCSV) {
          let progress = 0;
          progressInterval = setInterval(() => {
            progress = Math.min(progress + 1, 95); // Cap at 95% until complete
            setUploadedFiles(prev => prev.map(f => 
              f.id === tempId ? { ...f, uploadProgress: progress } : f
            ));
          }, 500); // Update every 500ms
        }

        let result;
        if (existingFileId) {
          result = await fetchBackend(`/files/update_file/${existingFileId}`, {
            method: 'PUT',
            body: formData,
          });
        } else {
          // Dynamic timeout based on file type
          // CSV: minimum 2 minutes, add 1 minute per MB
          // PDF: 1 minute base
          let timeoutMs = 60000; // 1 minute default
          if (isCSV) {
            const fileSizeMB = file.size / (1024 * 1024);
            // 2 minutes base + 1 minute per MB (capped at 30 minutes)
            timeoutMs = Math.min(120000 + (fileSizeMB * 60000), 1800000);
            console.log(`Setting CSV timeout to ${timeoutMs/1000} seconds for ${fileSizeMB.toFixed(2)} MB file`);
          }
          
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
          
          try {
            result = await fetchBackend('/files/add_file', {
              method: 'POST',
              body: formData,
              signal: controller.signal,
            });
          } finally {
            clearTimeout(timeoutId);
            if (progressInterval) clearInterval(progressInterval);
          }
        }
        
        setUploadedFiles(prev => prev.map(f => 
          f.id === tempId
            ? { 
                ...f, 
                status: 'success', 
                chunks: result.total_chunks, 
                backendFileId: result.file_id,
                uploadProgress: 100 
              }
            : f
        ));
      } catch (error) {
        console.error('File upload error:', error);
        setUploadedFiles(prev => prev.map(f => 
          f.id === tempId
            ? { 
                ...f, 
                status: 'error', 
                error: error instanceof Error ? 
                  (error.name === 'AbortError' ? 
                    'Upload timeout - file processing took too long' : 
                    error.message) : 
                  'Upload failed',
                uploadProgress: 0 
              }
            : f
        ));
      }
    });
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!window.confirm('Are you sure you want to delete this file?')) return;
    
    try {
      await fetchBackend(`/files/delete_file/${fileId}`, {
        method: 'DELETE',
      });
      setUploadedFiles(prev => prev.filter(f => f.backendFileId !== fileId));
    } catch (error) {
      console.error('Failed to delete file:', error);
      alert(`Failed to delete file: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    handleFileUpload(e.dataTransfer.files);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
                  <div className="logo">
                    <div className="medical-logo">
                      <div className="medical-cross">
                        <div className="cross-horizontal"></div>
                        <div className="cross-vertical"></div>
                      </div>
                      <Bot className="logo-icon" />
                    </div>
                    <div className="logo-text-container">
                      <h1 className="logo-text">MediRAG</h1>
                      <span className="logo-subtitle">Clinical Intelligence System</span>
                    </div>
                  </div>
          
          <div className="header-controls">
            <button
              onClick={toggleTheme}
              className="theme-toggle"
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            
            <nav className="nav">
              {[
                { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
                { id: 'upload' as const, label: 'Upload', icon: Upload },
                { id: 'status' as const, label: 'Status', icon: Activity },
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`nav-button ${activeTab === tab.id ? 'active' : ''}`}
                  >
                    <Icon size={16} />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
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
                          <div className="medical-stethoscope">
                            <Sparkles className="empty-icon" />
                          </div>
                          <h3 className="empty-title">Clinical Intelligence System</h3>
                          <p className="empty-subtitle">Query evidence-based medical literature and clinical guidelines. Select from these clinical scenarios:</p>
                  <div className="empty-suggestions">
                    {sampleQuestions.map((question, index) => (
                      <button
                        key={index}
                        className="suggestion-chip"
                        onClick={() => handleSampleQuestion(question)}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
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
                    {message.isTyping ? (
                      <div className="typing-indicator">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                    ) : (
                      <>
                        <div className="message-text">{message.content}</div>
                        {message.contextCount !== undefined && message.contextCount > 0 && (
                          <div className="message-sources">
                            <span className="sources-badge">
                              <Database size={12} />
                              {message.contextCount} sources
                            </span>
                          </div>
                        )}
                        <div className="message-meta">
                          {message.type === 'user' ? <User size={12} /> : <Bot size={12} />}
                          <span>{formatDate(message.timestamp)}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="input-container">
              <form onSubmit={handleSubmit} className="input-form">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                          placeholder="Ask medical questions (e.g., symptoms, treatments, medications)..."
                  disabled={isChatLoading}
                  className="input-field"
                  rows={1}
                  style={{
                    resize: 'none',
                    overflow: 'hidden',
                    height: 'auto',
                    minHeight: '2.75rem',
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 128) + 'px';
                  }}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isChatLoading}
                  className="send-button"
                >
                  {isChatLoading ? <Loader2 size={16} /> : <Send size={16} />}
                </button>
              </form>
              {messages.length > 0 && (
                <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
                  <button
                    onClick={clearChatHistory}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                    }}
                  >
                    Clear chat history
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'upload' && (
          <div className="upload-container">
            <div className="upload-content">
              <div className="upload-card">
                <h2 className="upload-title">
                  <Upload size={20} />
                  Clinical Document Repository
                </h2>
                <div 
                  className={`upload-area ${dragActive ? 'drag-active' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="upload-icon" />
                  <p className="upload-text">
                    {dragActive ? 'Drop files here' : 'Drop PDF or CSV files here'}
                  </p>
                  <p className="upload-subtext">or click to select medical files (PDF/CSV)</p>
                  <button className="upload-button">
                    <FileText size={16} />
                    Select Files
                  </button>
                  <div style={{ 
                    marginTop: '1rem', 
                    padding: '0.75rem', 
                    background: 'var(--info-bg, #e3f2fd)', 
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    color: 'var(--info-text, #1976d2)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <AlertCircle size={16} />
                    <span>CSV files may take 30-60 seconds to process as they're converted into medical documents</span>
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.csv"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  className="file-input"
                />
              </div>

              {uploadedFiles.length > 0 && (
                <div className="upload-card">
                  <h3 className="upload-title">
                    <FileText size={20} />
                    Uploaded Files ({uploadedFiles.length})
                  </h3>
                  <div className="file-list">
                    {uploadedFiles.map((file) => (
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
                                  {file.status === 'uploading' && (
                                    file.name.toLowerCase().endsWith('.csv') 
                                      ? `Processing CSV data... ${file.uploadProgress || 0}%` 
                                      : 'Uploading...'
                                  )}
                                  {file.status === 'success' && `Uploaded (${file.chunks} documents)`}
                                  {file.status === 'error' && (file.error || 'Upload failed')}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        {file.status === 'success' && file.backendFileId && (
                          <div className="file-actions">
                            <input
                              type="file"
                              accept=".pdf"
                              onChange={(e) => handleFileUpload(e.target.files, file.backendFileId!)}
                              style={{ display: 'none' }}
                              id={`update-file-${file.backendFileId}`}
                            />
                            <button 
                              onClick={() => document.getElementById(`update-file-${file.backendFileId}`)?.click()}
                              className="action-button update"
                            >
                              <RefreshCw size={14} />
                              Replace
                            </button>
                            <button 
                              onClick={() => handleDeleteFile(file.backendFileId!)}
                              className="action-button delete"
                            >
                              <Trash2 size={14} />
                              Delete
                            </button>
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
                    <span className="status-label">
                      <Zap size={16} style={{ marginRight: '0.5rem' }} />
                      Overall System
                    </span>
                    <div className="status-indicator">
                      {health?.overall ? (
                        <CheckCircle className="status-icon success" />
                      ) : (
                        <AlertCircle className="status-icon error" />
                      )}
                      <span className={`status-badge ${health?.overall ? 'healthy' : 'unhealthy'}`}>
                        {health?.overall ? (
                          <>
                            <CheckCircle size={12} />
                            Healthy
                          </>
                        ) : (
                          <>
                            <AlertCircle size={12} />
                            Unhealthy
                          </>
                        )}
                      </span>
                    </div>
                  </div>
                  <div className="status-item">
                    <span className="status-label">
                      <Database size={16} style={{ marginRight: '0.5rem' }} />
                      Vector Database
                    </span>
                    <div className="status-indicator">
                      {health?.vectordb ? (
                        <CheckCircle className="status-icon success" />
                      ) : (
                        <XCircle className="status-icon error" />
                      )}
                      <span className={`status-badge ${health?.vectordb ? 'healthy' : 'unhealthy'}`}>
                        {health?.vectordb ? (
                          <>
                            <CheckCircle size={12} />
                            Connected
                          </>
                        ) : (
                          <>
                            <XCircle size={12} />
                            Disconnected
                          </>
                        )}
                      </span>
                    </div>
                  </div>
                  <div className="status-item">
                    <span className="status-label">
                      <Brain size={16} style={{ marginRight: '0.5rem' }} />
                      LLM Service
                    </span>
                    <div className="status-indicator">
                      {health?.llm ? (
                        <CheckCircle className="status-icon success" />
                      ) : (
                        <XCircle className="status-icon error" />
                      )}
                      <span className={`status-badge ${health?.llm ? 'healthy' : 'unhealthy'}`}>
                        {health?.llm ? (
                          <>
                            <CheckCircle size={12} />
                            Operational
                          </>
                        ) : (
                          <>
                            <XCircle size={12} />
                            Down
                          </>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
                {health?.message && (
                  <div className="status-message">
                    <strong>System Message:</strong> {health.message}
                  </div>
                )}
                <button
                  onClick={checkSystemStatus}
                  className="refresh-button"
                >
                  <RefreshCw size={16} />
                  Refresh Status
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;