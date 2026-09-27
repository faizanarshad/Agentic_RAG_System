'use client';

import { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Upload,
  Send,
  Bot,
  User,
  Loader2,
  CheckCircle,
  XCircle,
  FileText,
  Trash2,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Database,
  Stethoscope,
} from 'lucide-react';
import { fetchBackend } from '@/lib/api';
import { initialView } from '@/lib/initial-view';

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
const formatDate = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};
// Medical sample questions for empty state
const sampleQuestions = [
  'What are the clinical manifestations of acute myocardial infarction?',
  'Explain the pharmacokinetics and contraindications of ACE inhibitors',
  'What are the SIRS criteria and sepsis diagnostic protocols?',
  'Describe the staging and management of chronic kidney disease',
  'What are the absolute contraindications for MRI contrast agents?',
  'Explain the pathophysiology and complications of Type 2 diabetes mellitus',
  'What are the common adverse effects of chemotherapy regimens?',
  'Describe the emergency management protocol for anaphylactic shock',
];
export default function MedicalWorkspace() {
  // State management
  const [medicalView, setMedicalView] = useState(() => initialView(['chat', 'upload'], 'chat'));
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.map((msg) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
      } catch {
        return [];
      }
    }
    return [];
  });
  const [input, setInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const successfulUploads = uploadedFiles.filter((f) => f.status === 'success').length;
  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  // Effects
  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, [messages]);
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  // Utility functions
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  const clearChatHistory = () => {
    if (window.confirm('Are you sure you want to clear all chat history?')) {
      setMessages([]);
      localStorage.removeItem('chatHistory');
    }
  };
  // API functions
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isChatLoading) return;
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsChatLoading(true);
    // Add typing indicator
    const typingMessage = {
      id: 'typing',
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isTyping: true,
    };
    setMessages((prev) => [...prev, typingMessage]);
    try {
      const data = await fetchBackend('/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input.trim() }),
      });
      // Remove typing indicator and add real response
      setMessages((prev) => {
        const filtered = prev.filter((msg) => msg.id !== 'typing');
        const assistantMessage = {
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
      setMessages((prev) => {
        const filtered = prev.filter((msg) => msg.id !== 'typing');
        const errorMessage = {
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
  const openMedicalChat = () => {
    setMedicalView('chat');
    setTimeout(() => inputRef.current?.focus(), 0);
  };
  const handleSampleQuestion = (question) => {
    setInput(question);
    inputRef.current?.focus();
  };
  const previewCSV = async (file) => {
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
  const handleFileUpload = async (files, existingFileId = null) => {
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
      const newFile = {
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
        setUploadedFiles((prev) => [...prev, newFile]);
      } else {
        setUploadedFiles((prev) => prev.map((f) => (f.id === tempId ? { ...f, ...newFile } : f)));
      }
      try {
        const formData = new FormData();
        formData.append('file', file);
        // Show progress animation for CSV files (they take longer)
        let progressInterval = null;
        if (isCSV) {
          let progress = 0;
          progressInterval = setInterval(() => {
            progress = Math.min(progress + 1, 95); // Cap at 95% until complete
            setUploadedFiles((prev) =>
              prev.map((f) => (f.id === tempId ? { ...f, uploadProgress: progress } : f)),
            );
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
            timeoutMs = Math.min(120000 + fileSizeMB * 60000, 1800000);
            console.log(
              `Setting CSV timeout to ${timeoutMs / 1000} seconds for ${fileSizeMB.toFixed(2)} MB file`,
            );
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
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === tempId
              ? {
                  ...f,
                  status: 'success',
                  chunks: result.total_chunks,
                  backendFileId: result.file_id,
                  uploadProgress: 100,
                }
              : f,
          ),
        );
      } catch (error) {
        console.error('File upload error:', error);
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === tempId
              ? {
                  ...f,
                  status: 'error',
                  error:
                    error instanceof Error
                      ? error.name === 'AbortError'
                        ? 'Upload timeout - file processing took too long'
                        : error.message
                      : 'Upload failed',
                  uploadProgress: 0,
                }
              : f,
          ),
        );
      }
    });
  };
  const handleDeleteFile = async (fileId) => {
    if (!window.confirm('Are you sure you want to delete this file?')) return;
    try {
      await fetchBackend(`/files/delete_file/${fileId}`, {
        method: 'DELETE',
      });
      setUploadedFiles((prev) => prev.filter((f) => f.backendFileId !== fileId));
    } catch (error) {
      console.error('Failed to delete file:', error);
      alert(`Failed to delete file: ${error instanceof Error ? error.message : String(error)}`);
    }
  };
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };
  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleFileUpload(e.dataTransfer.files);
  };
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  return (
    <div className="medical-page">
      <div className="medical-header">
        <div>
          <h2 className="legal-page-title">
            <Stethoscope size={22} /> Medical
          </h2>
          <p className="legal-muted">Upload clinical documents and ask questions grounded in them.</p>
        </div>
        <nav className="legal-subnav" aria-label="Medical views">
          <button
            onClick={() => setMedicalView('chat')}
            className={`nav-button ${medicalView === 'chat' ? 'active' : ''}`}
          >
            <MessageSquare size={16} />
            Chat
          </button>
          <button
            onClick={() => setMedicalView('upload')}
            className={`nav-button ${medicalView === 'upload' ? 'active' : ''}`}
          >
            <Upload size={16} />
            Documents
            {successfulUploads > 0 && <span className="medical-count">{successfulUploads}</span>}
          </button>
        </nav>
      </div>
      <div className="medical-body">
        {medicalView === 'chat' && (
          <div className="chat-container">
            {/* Messages */}
            <div className="messages">
              {messages.length === 0 && (
                <div className="empty-state">
                  <div className="medical-stethoscope">
                    <Sparkles className="empty-icon" />
                  </div>
                  <h3 className="empty-title">Clinical Intelligence System</h3>
                  <p className="empty-subtitle">
                    Query evidence-based medical literature and clinical guidelines. Select from these
                    clinical scenarios:
                  </p>
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
                  <button className="legal-link medical-upload-link" onClick={() => setMedicalView('upload')}>
                    <Upload size={14} />
                    Have your own clinical documents? Upload PDFs or CSVs to ground the answers in them
                  </button>
                </div>
              )}

              {messages.map((message) => (
                <div key={message.id} className={`message ${message.type}`}>
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
                    const target = e.target;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 128) + 'px';
                  }}
                />
                <button type="submit" disabled={!input.trim() || isChatLoading} className="send-button">
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

        {medicalView === 'upload' && (
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
                  <div
                    style={{
                      marginTop: '1rem',
                      padding: '0.75rem',
                      background: 'var(--info-bg, #e3f2fd)',
                      borderRadius: '0.5rem',
                      fontSize: '0.875rem',
                      color: 'var(--info-text, #1976d2)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                  >
                    <AlertCircle size={16} />
                    <span>
                      CSV files may take 30-60 seconds to process as they’re converted into medical documents
                    </span>
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
                  <div className="medical-files-header">
                    <h3 className="upload-title">
                      <FileText size={20} />
                      Uploaded Files ({uploadedFiles.length})
                    </h3>
                    {successfulUploads > 0 && (
                      <button className="upload-button" onClick={openMedicalChat}>
                        <MessageSquare size={16} />
                        Ask in chat
                      </button>
                    )}
                  </div>
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
                                  {file.status === 'uploading' &&
                                    (file.name.toLowerCase().endsWith('.csv')
                                      ? `Processing CSV data... ${file.uploadProgress || 0}%`
                                      : 'Uploading...')}
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
                              onChange={(e) => handleFileUpload(e.target.files, file.backendFileId)}
                              style={{ display: 'none' }}
                              id={`update-file-${file.backendFileId}`}
                            />
                            <button
                              onClick={() =>
                                document.getElementById(`update-file-${file.backendFileId}`)?.click()
                              }
                              className="action-button update"
                            >
                              <RefreshCw size={14} />
                              Replace
                            </button>
                            <button
                              onClick={() => handleDeleteFile(file.backendFileId)}
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
      </div>
    </div>
  );
}
