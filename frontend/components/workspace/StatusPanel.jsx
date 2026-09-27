'use client';

import { useEffect, useState } from 'react';
import { Activity, AlertCircle, Brain, CheckCircle, Database, RefreshCw, XCircle, Zap } from 'lucide-react';
import { fetchBackend } from '@/lib/api';

export default function StatusPanel() {
  const [health, setHealth] = useState(null);
  const checkSystemStatus = async () => {
    try {
      const [healthResponse, filesHealthResponse] = await Promise.all([
        fetchBackend('/health'),
        fetchBackend('/files/health'),
      ]);
      setHealth({
        overall: filesHealthResponse.overall,
        vectordb: filesHealthResponse.vectordb,
        llm: filesHealthResponse.llm,
        message: healthResponse.message,
      });
    } catch (error) {
      console.error('Status check failed:', error);
      setHealth({
        vectordb: false,
        llm: false,
        overall: false,
        message: `Status check failed: ${error instanceof Error ? error.message : String(error)}`,
      });
    }
  };
  useEffect(() => {
    // Poll the back end; state is only set after each request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);
  return (
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
          <button onClick={checkSystemStatus} className="refresh-button">
            <RefreshCw size={16} />
            Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
}
