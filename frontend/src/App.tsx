import React, { useState, useEffect } from 'react';
import './index.css';

// Backend API base URL
const API_BASE = 'http://localhost:8000';

async function chatApi(query: string) {
  const res = await fetch(`${API_BASE}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function uploadFileApi(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/files/add_file`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function deleteFileApi(fileId: string) {
  const res = await fetch(`${API_BASE}/files/delete_file/${encodeURIComponent(fileId)}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function updateFileApi(fileId: string, file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/files/update_file/${encodeURIComponent(fileId)}`, { method: 'PUT', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function healthApi() {
  const [health, filesHealth] = await Promise.all([
    fetch(`${API_BASE}/health`).then(r => r.json()).catch(() => ({ message: 'unavailable' })),
    fetch(`${API_BASE}/files/health`).then(r => r.json()).catch(() => ({ vectordb: false, llm: false, overall: false }))
  ]);
  return { health, filesHealth };
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: string;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: 'pending' | 'success' | 'error';
  chunks: number;
  fileId: string | null;
  error: string | null;
}

interface HealthStatus {
  vectordb: boolean;
  llm: boolean;
  overall: boolean;
}

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isChatLoading, setIsChatLoading] = useState(false);

  useEffect(() => {
    fetchHealthStatus();
  }, []);

  const fetchHealthStatus = async () => {
    try {
      const { filesHealth } = await healthApi();
      setHealth(filesHealth);
    } catch (error) {
      setHealth({ vectordb: false, llm: false, overall: false });
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (chatInput.trim() === '') return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      text: chatInput,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, newUserMessage]);
    const queryToSend = chatInput;
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await chatApi(queryToSend);
      const newAssistantMessage: Message = {
        id: Date.now().toString() + '-ai',
        text: response.answer,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, newAssistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        text: 'Error: Could not get a response from the RAG system.',
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files) return;

    Array.from(files).forEach(async (file) => {
      const tempId = crypto.randomUUID();
      const newFile: UploadedFile = {
        id: tempId,
        name: file.name,
        size: file.size,
        status: 'pending',
        chunks: 0,
        fileId: null,
        error: null,
      };
      setUploadedFiles(prev => [...prev, newFile]);

      try {
        const result = await uploadFileApi(file);
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === tempId
              ? { ...f, status: 'success', chunks: result.total_chunks ?? 0, fileId: result.file_id }
              : f
          )
        );
      } catch (error: any) {
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === tempId
              ? { ...f, status: 'error', error: error?.message || 'Upload failed' }
              : f
          )
        );
      }
    });
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await deleteFileApi(fileId);
      setUploadedFiles(prev => prev.filter(f => f.fileId !== fileId));
    } catch (error) {
      alert('Failed to delete file.');
    }
  };

  const handleReplaceFile = async (fileId: string) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf';
    input.onchange = async (e: any) => {
      const file: File | undefined = e.target.files?.[0];
      if (!file) return;
      try {
        const result = await updateFileApi(fileId, file);
        setUploadedFiles(prev => prev.map(f => (
          f.fileId === fileId ? { ...f, status: 'success', chunks: result.total_chunks ?? f.chunks } : f
        )));
      } catch (error: any) {
        setUploadedFiles(prev => prev.map(f => (
          f.fileId === fileId ? { ...f, status: 'error', error: error?.message || 'Update failed' } : f
        )));
      }
    };
    input.click();
  };

  return (
    <div className="container">
      <div className="header">Agentic RAG System</div>
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
        <button
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload
        </button>
        <button
          className={`tab-button ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
        >
          Status
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'chat' && (
          <div className="chat-container">
            <div className="messages">
              {messages.map(msg => (
                <div key={msg.id} className={`message ${msg.sender}`}>
                  <div className="message-bubble">
                    {msg.text}
                    <div className="message-timestamp">{msg.timestamp}</div>
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="message assistant">
                  <div className="message-bubble">Thinking...</div>
                </div>
              )}
            </div>
            <form onSubmit={handleChatSubmit} className="chat-input-form">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a question..."
                className="chat-input"
                disabled={isChatLoading}
              />
              <button type="submit" className="chat-send-button" disabled={isChatLoading}>
                Send
              </button>
            </form>
          </div>
        )}

        {activeTab === 'upload' && (
          <div>
            <div
              className="upload-area"
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('drag-active'); }}
              onDragLeave={(e) => { e.preventDefault(); e.currentTarget.classList.remove('drag-active'); }}
              onDrop={(e) => { e.preventDefault(); e.currentTarget.classList.remove('drag-active'); handleFileUpload(e.dataTransfer.files); }}
              onClick={() => document.getElementById('fileInput')?.click()}
            >
              <input
                id="fileInput"
                type="file"
                accept=".pdf"
                multiple
                onChange={(e) => handleFileUpload(e.target.files)}
                style={{ display: 'none' }}
              />
              <p>Drag & drop PDF files here, or click to select</p>
            </div>
            <ul className="file-list">
              {uploadedFiles.map(file => (
                <li key={file.id} className="file-item">
                  <div className="file-item-info">
                    <span className="file-item-name">{file.name}</span>
                    <span className="file-item-details">
                      {(file.size / 1024).toFixed(2)} KB | Chunks: {file.chunks}
                    </span>
                  </div>
                  <span className={`file-item-status ${file.status}`}>
                    {file.status === 'pending' && 'Uploading...'}
                    {file.status === 'success' && 'Uploaded'}
                    {file.status === 'error' && `Error: ${file.error}`}
                  </span>
                  {file.status === 'success' && file.fileId && (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => handleReplaceFile(file.fileId!)}
                        className="delete-button"
                        style={{ backgroundColor: '#6c757d' }}
                      >
                        Replace
                      </button>
                      <button
                        onClick={() => handleDeleteFile(file.fileId!)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === 'status' && health && (
          <div>
            <div className="status-grid">
              <div className="status-card">
                <span className={`status-icon ${health.vectordb ? 'success' : 'error'}`}>
                  {health.vectordb ? '✅' : '❌'}
                </span>
                <h3>Vector DB</h3>
                <p>{health.vectordb ? 'Operational' : 'Disconnected'}</p>
              </div>
              <div className="status-card">
                <span className={`status-icon ${health.llm ? 'success' : 'error'}`}>
                  {health.llm ? '✅' : '❌'}
                </span>
                <h3>LLM Service</h3>
                <p>{health.llm ? 'Operational' : 'Disconnected'}</p>
              </div>
              <div className="status-card">
                <span className={`status-icon ${health.overall ? 'success' : 'error'}`}>
                  {health.overall ? 'Healthy' : 'Degraded'}
                </span>
                <h3>Overall System</h3>
                <p>{health.overall ? 'All systems go!' : 'Issues detected'}</p>
              </div>
            </div>
            <button onClick={fetchHealthStatus} className="refresh-button">
              Refresh Status
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
