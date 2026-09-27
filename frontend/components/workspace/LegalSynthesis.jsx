'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  CalendarClock,
  CheckCircle,
  FileSearch,
  FileText,
  FolderOpen,
  Layers,
  Loader2,
  MessageSquare,
  RefreshCw,
  Scale,
  Search,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { fetchBackend } from '@/lib/api';
import { initialView } from '@/lib/initial-view';
// Constants
const MAX_BATCH_DOCS = 100;
const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.png', '.jpg', '.jpeg', '.tif', '.tiff'];
const DOC_TYPE_LABELS = {
  contract: 'Contract',
  court_filing: 'Court filing',
  case_file: 'Case file',
  compliance_record: 'Compliance record',
  other_legal: 'Other legal',
  non_legal: 'Non-legal',
};
const SYNTHESIS_EXAMPLES = [
  'How do limitation of liability and indemnification terms differ across our contracts, and which are most one-sided?',
  'What compliance findings recur across audits, and which remediation deadlines are at risk?',
  'Summarize the claims, relief sought and procedural posture across the litigation documents.',
  'Which agreements auto-renew or lack termination for convenience, and what are the notice periods?',
];
// Utility functions
const docTypeLabel = (docType) => (docType ? DOC_TYPE_LABELS[docType] || docType : 'Pending');
const humanize = (value) => value.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
const hasSupportedExtension = (name) =>
  SUPPORTED_EXTENSIONS.some((extension) => name.toLowerCase().endsWith(extension));
const RiskBadge = ({ level, score }) => {
  if (!level) return <span className="legal-badge neutral">Not assessed</span>;
  const Icon = level === 'high' ? AlertTriangle : level === 'medium' ? AlertCircle : CheckCircle;
  return (
    <span className={`legal-badge risk-${level}`}>
      <Icon size={12} />
      {humanize(level)} risk{score !== undefined && score !== null ? ` · ${score}` : ''}
    </span>
  );
};
const BarList = ({ items, formatLabel = (label) => label }) => {
  if (items.length === 0) return <p className="legal-empty-note">No data yet</p>;
  const max = Math.max(...items.map(([, value]) => value));
  return (
    <div className="legal-bars">
      {items.map(([label, value]) => (
        <div className="legal-bar-row" key={label} title={`${formatLabel(label)}: ${value}`}>
          <span className="legal-bar-label">{formatLabel(label)}</span>
          <div className="legal-bar-track">
            <div className="legal-bar-fill" style={{ width: `${Math.max((value / max) * 100, 2)}%` }} />
          </div>
          <span className="legal-bar-value">{value}</span>
        </div>
      ))}
    </div>
  );
};
const DocChips = ({ labels, documents, onOpen }) => (
  <span className="legal-chips">
    {labels.map((label) => {
      const document = documents.find((d) => d.label === label);
      return (
        <button
          key={label}
          className="legal-chip"
          title={document ? document.title || document.filename : label}
          onClick={() => document && onOpen(document.file_id)}
        >
          {label}
        </button>
      );
    })}
  </span>
);
const LegalSynthesis = () => {
  // State management
  const [view, setView] = useState(() => initialView(['overview', 'documents', 'synthesize', 'ask'], 'overview'));
  const [stats, setStats] = useState(null);
  const [batch, setBatch] = useState(null);
  const [uploadMessage, setUploadMessage] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [documentTotal, setDocumentTotal] = useState(0);
  const [filterType, setFilterType] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [filterSearch, setFilterSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [docQuestion, setDocQuestion] = useState('');
  const [docAnswer, setDocAnswer] = useState(null);
  const [isDocAsking, setIsDocAsking] = useState(false);
  const [synthQuestion, setSynthQuestion] = useState('');
  const [synthType, setSynthType] = useState('');
  const [synthRisk, setSynthRisk] = useState('');
  const [synthMax, setSynthMax] = useState(15);
  const [synthesis, setSynthesis] = useState(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [askQuery, setAskQuery] = useState('');
  const [askResult, setAskResult] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState(null);
  // Refs
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  // API functions
  const loadStats = useCallback(async () => {
    try {
      setStats(await fetchBackend('/legal/corpus/stats'));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);
  const loadDocuments = useCallback(async () => {
    const params = new URLSearchParams({ limit: '200' });
    if (filterType) params.set('doc_type', filterType);
    if (filterRisk) params.set('overall_risk', filterRisk);
    if (filterSearch.trim()) params.set('search', filterSearch.trim());
    try {
      const data = await fetchBackend(`/legal/documents?${params}`);
      setDocuments(data.documents);
      setDocumentTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [filterType, filterRisk, filterSearch]);
  const loadLatestBatch = useCallback(async () => {
    try {
      const data = await fetchBackend('/legal/batches/latest');
      setBatch(data.batch);
    } catch {
      // Progress is optional; the rest of the page still works
    }
  }, []);
  // Effects
  useEffect(() => {
    // Fetch on mount; state is only set after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadStats();
    loadLatestBatch();
  }, [loadStats, loadLatestBatch]);
  useEffect(() => {
    // Refetch when the view or filters change; state is set after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (view === 'documents') loadDocuments();
  }, [view, loadDocuments]);
  useEffect(() => {
    if (!batch || batch.finished) return;
    const interval = setInterval(async () => {
      try {
        const updated = await fetchBackend(`/legal/batches/${batch.id}`);
        setBatch(updated);
        if (updated.done !== batch.done || updated.finished) {
          loadStats();
          if (view === 'documents') loadDocuments();
        }
      } catch {
        // Keep polling; transient errors are expected while the server is busy
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [batch, view, loadStats, loadDocuments]);
  // Handlers
  const handleFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    const all = Array.from(fileList);
    const supported = all.filter((file) => hasSupportedExtension(file.name));
    const skipped = all.length - supported.length;
    const files = supported.slice(0, MAX_BATCH_DOCS);
    if (files.length === 0) {
      setUploadMessage('None of the selected files are supported (PDF, DOCX, TXT, MD, PNG, JPG, TIFF).');
      return;
    }
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    setIsUploading(true);
    setUploadMessage(null);
    setError(null);
    try {
      const data = await fetchBackend('/legal/batches', { method: 'POST', body: formData });
      setBatch(data.batch);
      const notes = [`Queued ${data.batch.total} documents for analysis.`];
      if (supported.length > MAX_BATCH_DOCS) notes.push(`Only the first ${MAX_BATCH_DOCS} were uploaded.`);
      if (skipped > 0) notes.push(`${skipped} unsupported files skipped.`);
      if (data.rejected.length > 0) notes.push(`${data.rejected.length} rejected by the server.`);
      setUploadMessage(notes.join(' '));
    } catch (e) {
      setUploadMessage(`Upload failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (folderInputRef.current) folderInputRef.current.value = '';
    }
  };
  const openDocument = async (id) => {
    setDocAnswer(null);
    setDocQuestion('');
    try {
      setSelected(await fetchBackend(`/legal/documents/${id}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  const retryDocument = async (id) => {
    try {
      await fetchBackend(`/legal/documents/${id}/retry`, { method: 'POST' });
      setSelected(null);
      loadDocuments();
      loadLatestBatch();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  const deleteDocument = async (id) => {
    if (!window.confirm('Delete this document and its analysis?')) return;
    try {
      await fetchBackend(`/legal/documents/${id}`, { method: 'DELETE' });
      setSelected(null);
      loadDocuments();
      loadStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  const askDocument = async (e) => {
    e.preventDefault();
    if (!selected || !docQuestion.trim()) return;
    setIsDocAsking(true);
    try {
      setDocAnswer(
        await fetchBackend('/legal/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: docQuestion.trim(), file_id: selected.id }),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsDocAsking(false);
    }
  };
  const runSynthesis = async (e) => {
    e.preventDefault();
    if (!synthQuestion.trim() || isSynthesizing) return;
    setIsSynthesizing(true);
    setSynthesis(null);
    setError(null);
    try {
      setSynthesis(
        await fetchBackend('/legal/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: synthQuestion.trim(),
            doc_type: synthType || null,
            overall_risk: synthRisk || null,
            max_documents: synthMax,
          }),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSynthesizing(false);
    }
  };
  const runAsk = async (mode) => {
    if (!askQuery.trim() || isAsking) return;
    setIsAsking(true);
    setError(null);
    try {
      if (mode === 'ask') {
        setSearchResults(null);
        setAskResult(
          await fetchBackend('/legal/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: askQuery.trim() }),
          }),
        );
      } else {
        setAskResult(null);
        const data = await fetchBackend('/legal/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: askQuery.trim(), top_k: 10 }),
        });
        setSearchResults(data.results);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsAsking(false);
    }
  };
  // Render helpers
  const renderBatchProgress = () => {
    if (!batch) return null;
    const percent = batch.total ? Math.round((batch.done / batch.total) * 100) : 0;
    const failed = batch.counts.failed || 0;
    return (
      <div className="legal-progress">
        <div className="legal-progress-header">
          <span>
            {batch.finished ? <CheckCircle size={14} /> : <Loader2 size={14} className="spin" />}
            {batch.finished ? 'Last batch complete' : 'Analyzing batch'}: {batch.done} of {batch.total}{' '}
            documents
          </span>
          <span>{percent}%</span>
        </div>
        <div
          className="legal-progress-track"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div className="legal-progress-fill" style={{ width: `${percent}%` }} />
        </div>
        <div className="legal-progress-meta">
          {batch.counts.completed || 0} completed · {batch.counts.processing || 0} processing ·{' '}
          {batch.counts.queued || 0} queued{failed > 0 ? ` · ${failed} failed` : ''}
        </div>
      </div>
    );
  };
  const renderOverview = () => (
    <>
      <div className="upload-card">
        <h2 className="upload-title">
          <Upload size={20} />
          Build the legal corpus
        </h2>
        <p className="legal-muted">
          Upload contracts, court filings, case files and compliance records (up to {MAX_BATCH_DOCS} per
          batch). Each document is OCR’d if scanned, classified, mined for parties, dates, clauses and
          obligations, risk-assessed, summarized and indexed for semantic search.
        </p>
        <div className="legal-upload-actions">
          <button
            className="upload-button"
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {isUploading ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
            Select files
          </button>
          <button
            className="upload-button secondary"
            disabled={isUploading}
            onClick={() => folderInputRef.current?.click()}
          >
            <FolderOpen size={16} />
            Select folder
          </button>
          <span className="legal-muted small">PDF (incl. scanned), DOCX, TXT, PNG, JPG, TIFF</span>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={SUPPORTED_EXTENSIONS.join(',')}
          onChange={(e) => handleFiles(e.target.files)}
          className="file-input"
        />
        <input
          ref={folderInputRef}
          type="file"
          multiple
          {...{ webkitdirectory: '' }}
          onChange={(e) => handleFiles(e.target.files)}
          className="file-input"
        />
        {uploadMessage && <p className="legal-note">{uploadMessage}</p>}
        {renderBatchProgress()}
      </div>

      {stats && (
        <>
          <div className="legal-tiles">
            <div className="legal-tile">
              <span className="legal-tile-label">Documents analyzed</span>
              <span className="legal-tile-value">{stats.completed}</span>
              <span className="legal-tile-sub">{stats.total} in corpus</span>
            </div>
            <div className="legal-tile">
              <span className="legal-tile-label">High-risk documents</span>
              <span className="legal-tile-value">{stats.by_risk.high}</span>
              <span className="legal-tile-sub">
                {stats.by_risk.medium} medium · {stats.by_risk.low} low
              </span>
            </div>
            <div className="legal-tile">
              <span className="legal-tile-label">Average risk score</span>
              <span className="legal-tile-value">{stats.average_risk_score ?? '—'}</span>
              <span className="legal-tile-sub">0 (low) to 100 (high)</span>
            </div>
            <div className="legal-tile">
              <span className="legal-tile-label">Pages processed</span>
              <span className="legal-tile-value">{stats.total_pages}</span>
              <span className="legal-tile-sub">{stats.ocr_pages} via OCR</span>
            </div>
          </div>

          <div className="legal-grid">
            <div className="upload-card">
              <h3 className="legal-card-title">
                <Layers size={16} /> Document types
              </h3>
              <BarList items={Object.entries(stats.by_doc_type)} formatLabel={docTypeLabel} />
            </div>
            <div className="upload-card">
              <h3 className="legal-card-title">
                <BarChart3 size={16} /> Risk categories
              </h3>
              <BarList items={stats.risk_categories} formatLabel={humanize} />
            </div>
            <div className="upload-card">
              <h3 className="legal-card-title">
                <Scale size={16} /> Governing law
              </h3>
              <BarList items={stats.governing_law} />
            </div>
            <div className="upload-card">
              <h3 className="legal-card-title">
                <AlertTriangle size={16} /> Highest-risk documents
              </h3>
              {stats.high_risk_documents.length === 0 ? (
                <p className="legal-empty-note">No high-risk documents</p>
              ) : (
                <ul className="legal-list">
                  {stats.high_risk_documents.map((d) => (
                    <li key={d.file_id}>
                      <button className="legal-link" onClick={() => openDocument(d.file_id)}>
                        {d.title}
                      </button>
                      <RiskBadge level="high" score={d.risk_score} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="upload-card legal-span-2">
              <h3 className="legal-card-title">
                <CalendarClock size={16} /> Upcoming deadlines &amp; key dates
              </h3>
              {stats.upcoming_deadlines.length === 0 ? (
                <p className="legal-empty-note">No upcoming dated obligations</p>
              ) : (
                <table className="legal-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>What</th>
                      <th>Document</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.upcoming_deadlines.map((d, i) => (
                      <tr key={`${d.file_id}-${i}`}>
                        <td className="nowrap">{d.date}</td>
                        <td>{d.description}</td>
                        <td>
                          <button className="legal-link" onClick={() => openDocument(d.file_id)}>
                            {d.document}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
  const renderDocuments = () => (
    <div className="upload-card">
      <div className="legal-filters">
        <div className="legal-search-field">
          <Search size={14} />
          <input
            value={filterSearch}
            onChange={(e) => setFilterSearch(e.target.value)}
            placeholder="Filter by title or filename"
          />
        </div>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">All types</option>
          {Object.entries(DOC_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select value={filterRisk} onChange={(e) => setFilterRisk(e.target.value)}>
          <option value="">All risk levels</option>
          <option value="high">High risk</option>
          <option value="medium">Medium risk</option>
          <option value="low">Low risk</option>
        </select>
        <button className="action-button update" onClick={loadDocuments}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
      <p className="legal-muted small">{documentTotal} documents</p>
      <div className="legal-table-wrap">
        <table className="legal-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Risk</th>
              <th>Governing law</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((d) => (
              <tr key={d.id} className="clickable" onClick={() => openDocument(d.id)}>
                <td>
                  <div className="legal-doc-title">{d.title || d.filename}</div>
                  <div className="legal-muted small">{d.filename}</div>
                </td>
                <td>
                  {docTypeLabel(d.doc_type)}
                  {d.subtype && <div className="legal-muted small">{d.subtype}</div>}
                </td>
                <td>
                  <RiskBadge level={d.overall_risk} score={d.risk_score} />
                </td>
                <td>{d.governing_law || '—'}</td>
                <td>
                  <span className={`legal-badge status-${d.status}`}>
                    {d.status === 'processing' && <Loader2 size={12} className="spin" />}
                    {humanize(d.status)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
  const renderSynthesis = () => (
    <>
      <div className="upload-card">
        <h2 className="upload-title">
          <Layers size={20} /> Cross-document synthesis
        </h2>
        <p className="legal-muted">
          A planning agent writes search queries, the most relevant documents are retrieved, an analysis agent
          reviews each one in parallel, and a synthesis agent combines the findings into a cited report.
        </p>
        <form onSubmit={runSynthesis}>
          <textarea
            className="legal-textarea"
            value={synthQuestion}
            onChange={(e) => setSynthQuestion(e.target.value)}
            placeholder="Ask a research question across the corpus…"
            rows={3}
          />
          <div className="legal-filters">
            <select value={synthType} onChange={(e) => setSynthType(e.target.value)}>
              <option value="">All document types</option>
              {Object.entries(DOC_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <select value={synthRisk} onChange={(e) => setSynthRisk(e.target.value)}>
              <option value="">All risk levels</option>
              <option value="high">High risk only</option>
              <option value="medium">Medium risk only</option>
              <option value="low">Low risk only</option>
            </select>
            <label className="legal-muted small">
              Documents to review
              <select value={synthMax} onChange={(e) => setSynthMax(Number(e.target.value))}>
                {[5, 10, 15, 25, 40].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              className="upload-button"
              disabled={!synthQuestion.trim() || isSynthesizing}
            >
              {isSynthesizing ? <Loader2 size={16} className="spin" /> : <Layers size={16} />}
              {isSynthesizing ? 'Synthesizing…' : 'Synthesize'}
            </button>
          </div>
        </form>
        {!synthesis && !isSynthesizing && (
          <div className="empty-suggestions">
            {SYNTHESIS_EXAMPLES.map((q) => (
              <button key={q} className="suggestion-chip" onClick={() => setSynthQuestion(q)}>
                {q}
              </button>
            ))}
          </div>
        )}
        {isSynthesizing && (
          <p className="legal-note">
            <Loader2 size={14} className="spin" /> Planning, retrieving and reviewing documents. This usually
            takes 20–60 seconds.
          </p>
        )}
      </div>

      {synthesis && (
        <>
          <div className="upload-card">
            <h3 className="legal-card-title">Executive summary</h3>
            <p className="legal-prose">{synthesis.report.executive_summary}</p>
            <p className="legal-muted small">
              {synthesis.documents_relevant} relevant of {synthesis.documents_reviewed} documents reviewed ·
              Search queries: {synthesis.plan.search_queries.join(' · ')}
            </p>
          </div>

          <div className="legal-grid">
            {(synthesis.report.themes?.length ?? 0) > 0 && (
              <div className="upload-card legal-span-2">
                <h3 className="legal-card-title">Themes</h3>
                {synthesis.report.themes.map((t, i) => (
                  <div key={i} className="legal-item">
                    <div className="legal-item-title">
                      {t.title}{' '}
                      <DocChips labels={t.documents} documents={synthesis.documents} onOpen={openDocument} />
                    </div>
                    <p>{t.insight}</p>
                  </div>
                ))}
              </div>
            )}
            {(synthesis.report.comparisons?.length ?? 0) > 0 && (
              <div className="upload-card">
                <h3 className="legal-card-title">Comparisons</h3>
                {synthesis.report.comparisons.map((c, i) => (
                  <div key={i} className="legal-item">
                    <div className="legal-item-title">
                      {c.topic}{' '}
                      <DocChips labels={c.documents} documents={synthesis.documents} onOpen={openDocument} />
                    </div>
                    <p>{c.observation}</p>
                  </div>
                ))}
              </div>
            )}
            {(synthesis.report.risks?.length ?? 0) > 0 && (
              <div className="upload-card">
                <h3 className="legal-card-title">Risks</h3>
                {synthesis.report.risks.map((r, i) => (
                  <div key={i} className="legal-item">
                    <div className="legal-item-title">
                      <RiskBadge level={r.severity} /> {r.title}{' '}
                      <DocChips labels={r.documents} documents={synthesis.documents} onOpen={openDocument} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            {(synthesis.report.outliers?.length ?? 0) > 0 && (
              <div className="upload-card">
                <h3 className="legal-card-title">Outliers</h3>
                {synthesis.report.outliers.map((o, i) => (
                  <div key={i} className="legal-item">
                    <div className="legal-item-title">
                      <DocChips labels={[o.document]} documents={synthesis.documents} onOpen={openDocument} />
                    </div>
                    <p>{o.note}</p>
                  </div>
                ))}
              </div>
            )}
            {(synthesis.report.recommendations?.length ?? 0) > 0 && (
              <div className="upload-card">
                <h3 className="legal-card-title">Recommendations</h3>
                <ul className="legal-bullets">
                  {synthesis.report.recommendations.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
                {synthesis.report.limitations && (
                  <p className="legal-muted small">Limitations: {synthesis.report.limitations}</p>
                )}
              </div>
            )}
          </div>

          <div className="upload-card">
            <h3 className="legal-card-title">Documents reviewed</h3>
            {synthesis.documents.map((d) => (
              <div key={d.label} className={`legal-item ${d.relevant ? '' : 'dimmed'}`}>
                <div className="legal-item-title">
                  <span className="legal-chip static">{d.label}</span>
                  <button className="legal-link" onClick={() => openDocument(d.file_id)}>
                    {d.title || d.filename}
                  </button>
                  <span className="legal-muted small">
                    {d.subtype || docTypeLabel(d.doc_type)} · relevance {d.score}
                  </span>
                  {!d.relevant && <span className="legal-badge neutral">Not relevant</span>}
                </div>
                {d.findings.length > 0 && (
                  <ul className="legal-bullets">
                    {d.findings.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                )}
                {d.evidence.slice(0, 2).map((ev, i) => (
                  <blockquote key={i} className="legal-quote">
                    “{ev.quote}”
                    {ev.section ? <span className="legal-muted small"> — {ev.section}</span> : null}
                  </blockquote>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
      <p className="legal-disclaimer">
        AI-generated analysis for research support. Not legal advice. Verify against the source documents.
      </p>
    </>
  );
  const renderAsk = () => (
    <>
      <div className="upload-card">
        <h2 className="upload-title">
          <MessageSquare size={20} /> Ask or search the corpus
        </h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            runAsk('ask');
          }}
        >
          <textarea
            className="legal-textarea"
            value={askQuery}
            onChange={(e) => setAskQuery(e.target.value)}
            placeholder="e.g. Which agreements are governed by Delaware law and what are their liability caps?"
            rows={2}
          />
          <div className="legal-filters">
            <button type="submit" className="upload-button" disabled={!askQuery.trim() || isAsking}>
              {isAsking ? <Loader2 size={16} className="spin" /> : <MessageSquare size={16} />}
              Ask with citations
            </button>
            <button
              type="button"
              className="upload-button secondary"
              disabled={!askQuery.trim() || isAsking}
              onClick={() => runAsk('search')}
            >
              <FileSearch size={16} />
              Semantic search
            </button>
          </div>
        </form>
      </div>

      {askResult && (
        <div className="upload-card">
          <h3 className="legal-card-title">Answer</h3>
          <p className="legal-prose">{askResult.answer}</p>
          <p className="legal-muted small">
            Confidence: {askResult.confidence || 'n/a'} · Strategy: {humanize(askResult.strategy)}
          </p>
          {askResult.sources.map((s) => (
            <div key={s.label} className="legal-item">
              <div className="legal-item-title">
                <span className="legal-chip static">{s.label}</span>
                <button className="legal-link" onClick={() => openDocument(s.file_id)}>
                  {s.title || s.filename}
                </button>
                {s.score !== null && <span className="legal-muted small">score {s.score}</span>}
              </div>
              <p className="legal-excerpt">{s.excerpt}</p>
            </div>
          ))}
        </div>
      )}

      {searchResults && (
        <div className="upload-card">
          <h3 className="legal-card-title">{searchResults.length} matching passages</h3>
          {searchResults.map((r, i) => (
            <div key={i} className="legal-item">
              <div className="legal-item-title">
                <button className="legal-link" onClick={() => openDocument(r.file_id)}>
                  {r.title || r.filename}
                </button>
                <span className="legal-muted small">
                  {docTypeLabel(r.doc_type)} · score {r.score}
                </span>
              </div>
              <p className="legal-excerpt">{r.text}</p>
            </div>
          ))}
        </div>
      )}
      <p className="legal-disclaimer">AI-generated answers for research support. Not legal advice.</p>
    </>
  );
  const renderDetail = () => {
    if (!selected) return null;
    const extraction = selected.extraction || {};
    const fields = Object.entries(extraction.fields || {}).filter(([, value]) => value);
    return (
      <div className="legal-drawer-backdrop" onClick={() => setSelected(null)}>
        <aside className="legal-drawer" onClick={(e) => e.stopPropagation()} aria-label="Document analysis">
          <div className="legal-drawer-header">
            <div>
              <h2>{selected.title || selected.filename}</h2>
              <p className="legal-muted small">
                {selected.filename} · {selected.subtype || docTypeLabel(selected.doc_type)}
                {selected.page_count ? ` · ${selected.page_count} pages` : ''}
                {selected.ocr_pages?.length ? ` · ${selected.ocr_pages.length} OCR'd` : ''}
              </p>
            </div>
            <button className="theme-toggle" onClick={() => setSelected(null)} aria-label="Close">
              <X size={18} />
            </button>
          </div>

          <div className="legal-drawer-actions">
            <RiskBadge level={selected.overall_risk} score={selected.risk_score} />
            <span className={`legal-badge status-${selected.status}`}>{humanize(selected.status)}</span>
            <button className="action-button update" onClick={() => retryDocument(selected.id)}>
              <RefreshCw size={14} /> Re-analyze
            </button>
            <button className="action-button delete" onClick={() => deleteDocument(selected.id)}>
              <Trash2 size={14} /> Delete
            </button>
          </div>
          {selected.error && <p className="legal-error">{selected.error}</p>}

          {selected.summary && (
            <section>
              <h3>Summary</h3>
              <p className="legal-prose">{selected.summary.summary}</p>
              <ul className="legal-bullets">
                {selected.summary.key_points.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h3>Ask this document</h3>
            <form onSubmit={askDocument} className="legal-inline-form">
              <input
                value={docQuestion}
                onChange={(e) => setDocQuestion(e.target.value)}
                placeholder="e.g. What is the notice period for termination?"
              />
              <button type="submit" className="upload-button" disabled={!docQuestion.trim() || isDocAsking}>
                {isDocAsking ? <Loader2 size={16} className="spin" /> : <MessageSquare size={16} />}
                Ask
              </button>
            </form>
            {docAnswer && <p className="legal-prose legal-answer">{docAnswer.answer}</p>}
          </section>

          {fields.length > 0 && (
            <section>
              <h3>Key terms</h3>
              <dl className="legal-fields">
                {fields.map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt>{humanize(key)}</dt>
                    <dd>{value}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </section>
          )}

          {(extraction.parties?.length ?? 0) > 0 && (
            <section>
              <h3>Parties</h3>
              <ul className="legal-bullets">
                {extraction.parties.map((p, i) => (
                  <li key={i}>
                    <strong>{p.name}</strong> — {p.role}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {selected.risks && selected.risks.risks.length > 0 && (
            <section>
              <h3>Risks</h3>
              {selected.risks.risks.map((r, i) => (
                <div key={i} className="legal-item">
                  <div className="legal-item-title">
                    <RiskBadge level={r.severity} /> {r.title}
                    {r.section && <span className="legal-muted small">{r.section}</span>}
                  </div>
                  <p>{r.explanation}</p>
                  <p className="legal-muted small">
                    <strong>Recommendation:</strong> {r.recommendation}
                  </p>
                </div>
              ))}
              {(selected.risks.missing_protections?.length ?? 0) > 0 && (
                <p className="legal-muted small">
                  Missing protections: {selected.risks.missing_protections.join('; ')}
                </p>
              )}
            </section>
          )}

          {(extraction.obligations?.length ?? 0) > 0 && (
            <section>
              <h3>Obligations</h3>
              <table className="legal-table">
                <thead>
                  <tr>
                    <th>Party</th>
                    <th>Obligation</th>
                    <th>Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {extraction.obligations.map((o, i) => (
                    <tr key={i}>
                      <td>{o.party}</td>
                      <td>{o.obligation}</td>
                      <td className="nowrap">{o.deadline || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {(extraction.key_dates?.length ?? 0) > 0 && (
            <section>
              <h3>Key dates</h3>
              <ul className="legal-bullets">
                {extraction.key_dates.map((d, i) => (
                  <li key={i}>
                    <strong>{d.date}</strong> — {d.label}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(extraction.clauses?.length ?? 0) > 0 && (
            <section>
              <h3>Key clauses</h3>
              {extraction.clauses.map((c, i) => (
                <div key={i} className="legal-item">
                  <div className="legal-item-title">
                    {c.title}
                    {c.section && <span className="legal-muted small">{c.section}</span>}
                  </div>
                  <blockquote className="legal-quote">{c.excerpt}</blockquote>
                </div>
              ))}
            </section>
          )}

          {selected.classification?.reasoning && (
            <p className="legal-muted small">
              Classification: {selected.classification.reasoning}
              {selected.classification.confidence !== undefined &&
                ` (confidence ${selected.classification.confidence})`}
            </p>
          )}
          <p className="legal-disclaimer">AI-generated analysis. Not legal advice.</p>
        </aside>
      </div>
    );
  };
  return (
    <div className="upload-container">
      <div className="upload-content legal-content">
        <div className="legal-header">
          <div>
            <h2 className="legal-page-title">
              <Scale size={22} /> Legal Data Synthesis
            </h2>
            <p className="legal-muted">
              Agentic analysis of contracts, filings, case files and compliance records.
            </p>
          </div>
          <nav className="legal-subnav" aria-label="Legal views">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'documents', label: 'Documents', icon: FileText },
              { id: 'synthesize', label: 'Synthesize', icon: Layers },
              { id: 'ask', label: 'Ask & Search', icon: MessageSquare },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setView(tab.id)}
                  className={`nav-button ${view === tab.id ? 'active' : ''}`}
                >
                  <Icon size={16} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {error && (
          <div className="legal-error">
            <AlertCircle size={16} /> {error}
            <button className="legal-link" onClick={() => setError(null)}>
              Dismiss
            </button>
          </div>
        )}

        {view === 'overview' && renderOverview()}
        {view === 'documents' && renderDocuments()}
        {view === 'synthesize' && renderSynthesis()}
        {view === 'ask' && renderAsk()}
      </div>
      {renderDetail()}
    </div>
  );
};
export default LegalSynthesis;
