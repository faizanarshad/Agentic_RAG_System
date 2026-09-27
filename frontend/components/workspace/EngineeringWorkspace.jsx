'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  CheckCircle,
  ClipboardCheck,
  Copy,
  Download,
  FileText,
  GitCompare,
  Info,
  LayoutTemplate,
  Loader2,
  MessageSquare,
  Plus,
  RefreshCw,
  Ruler,
  Save,
  Send,
  Sparkles,
  Trash2,
  Upload,
  XCircle,
} from 'lucide-react';
import { API_BASE, fetchBackend } from '@/lib/api';
import { initialView } from '@/lib/initial-view';
// Constants
const ACCEPTED = '.pdf,.png,.jpg,.jpeg,.tif,.tiff,.dxf';
const SEVERITIES = ['critical', 'major', 'minor', 'info'];
const VERDICT_LABELS = {
  approved: 'Approved',
  approved_with_comments: 'Approved with comments',
  rejected: 'Rejected',
};
// Utility functions
const humanize = (value) => value.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
const errorText = (e) => (e instanceof Error ? e.message : String(e));
// Model output is usually text but can be a structured value; never hand an object to React
const asText = (value) => {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(asText).join('; ');
  if (typeof value === 'object') {
    return Object.entries(value)
      .filter(([, v]) => v !== null && v !== '')
      .map(([k, v]) => `${k}: ${asText(v)}`)
      .join(', ');
  }
  return String(value);
};
const SeverityBadge = ({ severity }) => {
  const Icon =
    severity === 'critical'
      ? XCircle
      : severity === 'major'
        ? AlertTriangle
        : severity === 'minor'
          ? AlertCircle
          : Info;
  return (
    <span className={`legal-badge sev-${severity}`}>
      <Icon size={12} />
      {humanize(severity)}
    </span>
  );
};
const VerdictBadge = ({ verdict }) => {
  if (!verdict) return <span className="legal-badge neutral">Not reviewed</span>;
  const Icon = verdict === 'approved' ? CheckCircle : verdict === 'rejected' ? XCircle : AlertTriangle;
  const tone = verdict === 'approved' ? 'risk-low' : verdict === 'rejected' ? 'risk-high' : 'risk-medium';
  return (
    <span className={`legal-badge ${tone}`}>
      <Icon size={12} />
      {VERDICT_LABELS[verdict]}
    </span>
  );
};
const emptyTemplate = () => ({
  name: 'New template',
  description: '',
  category: 'custom',
  sections: [
    { title: 'Section 1', guidance: '', fields: [{ name: 'Field 1', type: 'text', required: true }] },
  ],
});
const EngineeringWorkspace = () => {
  // State management
  const [view, setView] = useState(() => initialView(['review', 'compare', 'templates', 'documents'], 'review'));
  const [error, setError] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [selected, setSelected] = useState(null);
  const [page, setPage] = useState(1);
  const [standard, setStandard] = useState('ISO');
  const [isReviewing, setIsReviewing] = useState(false);
  const [chat, setChat] = useState([]);
  const [question, setQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [compareA, setCompareA] = useState('');
  const [compareB, setCompareB] = useState('');
  const [comparison, setComparison] = useState(null);
  const [comparisons, setComparisons] = useState([]);
  const [isComparing, setIsComparing] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [draft, setDraft] = useState(null);
  const [templateReview, setTemplateReview] = useState(null);
  const [templateBusy, setTemplateBusy] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [generateTemplate, setGenerateTemplate] = useState('builtin-ecn');
  const [generateDrawings, setGenerateDrawings] = useState([]);
  const [generateComparisons, setGenerateComparisons] = useState([]);
  const [instructions, setInstructions] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [openDocument, setOpenDocument] = useState(null);
  const [documentSaved, setDocumentSaved] = useState(true);
  // Refs
  const drawingInputRef = useRef(null);
  const templateInputRef = useRef(null);
  // API functions
  const loadDrawings = useCallback(async () => {
    try {
      setDrawings((await fetchBackend('/engineering/drawings')).drawings);
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
  const loadTemplates = useCallback(async () => {
    try {
      setTemplates((await fetchBackend('/engineering/templates')).templates);
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
  const loadDocuments = useCallback(async () => {
    try {
      setDocuments((await fetchBackend('/engineering/documents')).documents);
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
  const loadComparisons = useCallback(async () => {
    try {
      setComparisons((await fetchBackend('/engineering/comparisons')).comparisons);
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
  // Effects
  useEffect(() => {
    // Fetch on mount; state is only set after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDrawings();
    loadTemplates();
    loadDocuments();
    loadComparisons();
  }, [loadDrawings, loadTemplates, loadDocuments, loadComparisons]);
  // Handlers: review
  const selectDrawing = async (id) => {
    try {
      const detail = await fetchBackend(`/engineering/drawings/${id}`);
      setSelected(detail);
      setPage(1);
      setChat([]);
    } catch (e) {
      setError(errorText(e));
    }
  };
  const uploadDrawing = async (files) => {
    if (!files || files.length === 0) return;
    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('standard', standard);
    setIsReviewing(true);
    setError(null);
    try {
      const detail = await fetchBackend('/engineering/drawings', { method: 'POST', body: formData });
      setSelected(detail);
      setPage(1);
      setChat([]);
      loadDrawings();
      if (detail.status === 'failed') setError(`Review failed: ${detail.error}`);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setIsReviewing(false);
      if (drawingInputRef.current) drawingInputRef.current.value = '';
    }
  };
  const rerunReview = async () => {
    if (!selected) return;
    setIsReviewing(true);
    setError(null);
    try {
      const detail = await fetchBackend(`/engineering/drawings/${selected.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ standard }),
      });
      setSelected(detail);
      loadDrawings();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setIsReviewing(false);
    }
  };
  const deleteDrawing = async (id) => {
    if (!window.confirm('Delete this drawing and its review?')) return;
    try {
      await fetchBackend(`/engineering/drawings/${id}`, { method: 'DELETE' });
      if (selected?.id === id) setSelected(null);
      loadDrawings();
    } catch (e) {
      setError(errorText(e));
    }
  };
  const askQuestion = async (e) => {
    e.preventDefault();
    if (!selected || !question.trim() || isAsking) return;
    const turn = { role: 'user', content: question.trim() };
    const history = [...chat, turn];
    setChat(history);
    setQuestion('');
    setIsAsking(true);
    try {
      const data = await fetchBackend(`/engineering/drawings/${selected.id}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: turn.content, history: chat }),
      });
      setChat([...history, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      setChat([...history, { role: 'assistant', content: `Error: ${errorText(err)}` }]);
    } finally {
      setIsAsking(false);
    }
  };
  // Handlers: compare
  const runComparison = async () => {
    if (!compareA || !compareB) return;
    setIsComparing(true);
    setComparison(null);
    setError(null);
    try {
      setComparison(
        await fetchBackend('/engineering/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ a_id: compareA, b_id: compareB }),
        }),
      );
      loadComparisons();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setIsComparing(false);
    }
  };
  const draftEcnFromComparison = () => {
    if (!comparison) return;
    setGenerateTemplate('builtin-ecn');
    setGenerateDrawings([comparison.b.id]);
    setGenerateComparisons([comparison.id]);
    setOpenDocument(null);
    setView('documents');
  };
  // Handlers: templates
  const editTemplate = (template) => {
    setDraft(JSON.parse(JSON.stringify(template)));
    setTemplateReview(null);
  };
  const updateDraft = (mutate) => {
    setDraft((current) => {
      if (!current) return current;
      const next = JSON.parse(JSON.stringify(current));
      mutate(next);
      return next;
    });
  };
  const saveTemplate = async () => {
    if (!draft) return;
    setTemplateBusy('save');
    setError(null);
    try {
      const body = JSON.stringify({
        name: draft.name,
        description: draft.description,
        category: draft.category,
        sections: draft.sections,
      });
      const saved = draft.id
        ? await fetchBackend(`/engineering/templates/${draft.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body,
          })
        : await fetchBackend('/engineering/templates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body,
          });
      setDraft(saved);
      loadTemplates();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setTemplateBusy(null);
    }
  };
  const deleteTemplate = async () => {
    if (!draft?.id || draft.builtin || !window.confirm('Delete this template?')) return;
    try {
      await fetchBackend(`/engineering/templates/${draft.id}`, { method: 'DELETE' });
      setDraft(null);
      loadTemplates();
    } catch (e) {
      setError(errorText(e));
    }
  };
  const reviewTemplate = async () => {
    if (!draft?.id) return;
    setTemplateBusy('review');
    setError(null);
    try {
      setTemplateReview(await fetchBackend(`/engineering/templates/${draft.id}/review`, { method: 'POST' }));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setTemplateBusy(null);
    }
  };
  const applyRevisedTemplate = () => {
    if (!templateReview || !draft) return;
    setDraft({ ...templateReview.revised_template, id: draft.id, builtin: draft.builtin });
    setTemplateReview(null);
  };
  const importTemplate = async (files) => {
    if (!files || files.length === 0) return;
    const formData = new FormData();
    formData.append('file', files[0]);
    setTemplateBusy('import');
    setError(null);
    try {
      const imported = await fetchBackend('/engineering/templates/import', {
        method: 'POST',
        body: formData,
      });
      loadTemplates();
      editTemplate(imported);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setTemplateBusy(null);
      if (templateInputRef.current) templateInputRef.current.value = '';
    }
  };
  // Handlers: documents
  const toggle = (list, id) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  const generateDocument = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const doc = await fetchBackend('/engineering/documents/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: generateTemplate,
          drawing_ids: generateDrawings,
          comparison_ids: generateComparisons,
          instructions,
        }),
      });
      setOpenDocument(doc);
      setDocumentSaved(true);
      loadDocuments();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setIsGenerating(false);
    }
  };
  const loadDocument = async (id) => {
    try {
      setOpenDocument(await fetchBackend(`/engineering/documents/${id}`));
      setDocumentSaved(true);
    } catch (e) {
      setError(errorText(e));
    }
  };
  const editDocumentField = (sectionIndex, field, value) => {
    setOpenDocument((doc) => {
      if (!doc) return doc;
      const sections = doc.sections.map((s, i) =>
        i === sectionIndex ? { ...s, fields: { ...s.fields, [field]: value } } : s,
      );
      return { ...doc, sections };
    });
    setDocumentSaved(false);
  };
  const saveDocument = async () => {
    if (!openDocument) return;
    try {
      await fetchBackend(`/engineering/documents/${openDocument.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: openDocument.title, sections: openDocument.sections }),
      });
      setDocumentSaved(true);
      loadDocuments();
    } catch (e) {
      setError(errorText(e));
    }
  };
  const deleteDocument = async () => {
    if (!openDocument || !window.confirm('Delete this document?')) return;
    try {
      await fetchBackend(`/engineering/documents/${openDocument.id}`, { method: 'DELETE' });
      setOpenDocument(null);
      loadDocuments();
    } catch (e) {
      setError(errorText(e));
    }
  };
  const templateFieldType = (sectionTitle, fieldName) => {
    const template = templates.find((t) => t.id === openDocument?.template_id);
    const section = template?.sections.find((s) => s.title === sectionTitle);
    return section?.fields.find((f) => f.name === fieldName)?.type || 'text';
  };
  const reviewedDrawings = drawings.filter((d) => d.status === 'completed');
  // Render helpers
  const renderLibrary = () => (
    <div className="upload-card">
      <h3 className="legal-card-title">
        <FileText size={16} /> Drawing library ({drawings.length})
      </h3>
      {drawings.length === 0 ? (
        <p className="legal-empty-note">No drawings yet. Upload one above.</p>
      ) : (
        <div className="legal-table-wrap">
          <table className="legal-table">
            <thead>
              <tr>
                <th>Drawing</th>
                <th>Rev</th>
                <th>Verdict</th>
                <th>Findings</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {drawings.map((d) => (
                <tr
                  key={d.id}
                  className={`clickable ${selected?.id === d.id ? 'selected' : ''}`}
                  onClick={() => selectDrawing(d.id)}
                >
                  <td>
                    <div className="legal-doc-title">
                      {d.drawing_number ? `${d.drawing_number} · ${d.title || ''}` : d.filename}
                    </div>
                    <div className="legal-muted small">
                      {d.filename} · {d.standard}
                      {d.source_type ? ` · ${d.source_type.toUpperCase()}` : ''}
                    </div>
                  </td>
                  <td>{d.revision || '—'}</td>
                  <td>
                    {d.status === 'completed' ? (
                      <VerdictBadge verdict={d.verdict} />
                    ) : (
                      <span className={`legal-badge status-${d.status}`}>{humanize(d.status)}</span>
                    )}
                  </td>
                  <td className="nowrap">
                    {SEVERITIES.filter((s) => d.finding_counts[s] > 0).map((s) => (
                      <span key={s} className={`eng-count sev-${s}`} title={`${d.finding_counts[s]} ${s}`}>
                        {d.finding_counts[s]} {s}
                      </span>
                    ))}
                  </td>
                  <td>
                    <button
                      className="action-button delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteDrawing(d.id);
                      }}
                      aria-label="Delete drawing"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
  const renderDrawingDetail = () => {
    if (!selected) return null;
    const review = selected.review;
    const extraction = selected.extraction || {};
    const titleBlock = Object.entries(extraction.title_block || {});
    const failedRules = (selected.rule_checks || []).filter((r) => r.status === 'fail');
    return (
      <div className="eng-detail">
        <div className="upload-card eng-sheet-card">
          <div className="eng-sheet-header">
            <h3 className="legal-card-title">
              <Ruler size={16} /> {selected.filename}
            </h3>
            {selected.pages.length > 1 && (
              <select value={page} onChange={(e) => setPage(Number(e.target.value))} aria-label="Sheet">
                {selected.pages.map((p) => (
                  <option key={p.number} value={p.number}>
                    Sheet {p.number}
                  </option>
                ))}
              </select>
            )}
          </div>
          {selected.pages.length > 0 ? (
            <a
              href={`${API_BASE}/engineering/drawings/${selected.id}/pages/${page}`}
              target="_blank"
              rel="noreferrer"
              title="Open full size"
            >
              {/* Served by the back-end API (not a static asset), so next/image optimisation does not apply */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className="eng-sheet"
                src={`${API_BASE}/engineering/drawings/${selected.id}/pages/${page}`}
                alt={`Sheet ${page} of ${selected.filename}`}
                width={selected.pages.find((p) => p.number === page)?.width}
                height={selected.pages.find((p) => p.number === page)?.height}
                decoding="async"
              />
            </a>
          ) : (
            <p className="legal-empty-note">No rendered sheets.</p>
          )}
          {selected.cad && (
            <p className="legal-muted small">
              CAD units: {selected.cad.units} · Layers: {selected.cad.layers.join(', ')}
            </p>
          )}

          <div className="eng-ask">
            <h3 className="legal-card-title">
              <MessageSquare size={16} /> Ask about this drawing
            </h3>
            <div className="eng-chat">
              {chat.length === 0 && (
                <p className="legal-empty-note">
                  e.g. “Which features are controlled by datum A?” or “What is the tolerance on the Ø30 bore?”
                </p>
              )}
              {chat.map((turn, i) => (
                <div key={i} className={`eng-turn ${turn.role}`}>
                  {turn.content}
                </div>
              ))}
              {isAsking && (
                <div className="eng-turn assistant">
                  <Loader2 size={14} className="spin" /> Reading the drawing…
                </div>
              )}
            </div>
            <form className="legal-inline-form" onSubmit={askQuestion}>
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about the drawing"
              />
              <button type="submit" className="upload-button" disabled={!question.trim() || isAsking}>
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>

        <div className="eng-results">
          <div className="upload-card">
            <div className="eng-verdict-row">
              <VerdictBadge verdict={review?.verdict} />
              <span className="legal-muted small">Checked against {selected.standard}</span>
              <div className="eng-rerun">
                <select value={standard} onChange={(e) => setStandard(e.target.value)} aria-label="Standard">
                  <option value="ISO">ISO</option>
                  <option value="ASME">ASME</option>
                </select>
                <button className="action-button update" onClick={rerunReview} disabled={isReviewing}>
                  {isReviewing ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />} Re-review
                </button>
              </div>
            </div>
            {selected.status === 'failed' && <p className="legal-error">{selected.error}</p>}
            {review && <p className="legal-prose">{review.summary}</p>}
          </div>

          {review && (
            <div className="upload-card">
              <h3 className="legal-card-title">
                <ClipboardCheck size={16} /> Findings ({review.findings.length})
              </h3>
              {review.findings.length === 0 && <p className="legal-empty-note">No issues found.</p>}
              {review.findings.map((f, i) => (
                <div key={i} className="legal-item">
                  <div className="legal-item-title">
                    <SeverityBadge severity={f.severity} />
                    {f.title}
                    <span className="legal-muted small">{humanize(f.category)}</span>
                  </div>
                  <p>{asText(f.description)}</p>
                  <p className="legal-muted small">
                    <strong>Location:</strong> {asText(f.location)}
                  </p>
                  <p className="legal-muted small">
                    <strong>Fix:</strong> {asText(f.recommendation)}
                  </p>
                </div>
              ))}
            </div>
          )}

          {selected.rule_checks && (
            <div className="upload-card">
              <h3 className="legal-card-title">
                <CheckCircle size={16} /> Automated checks ({failedRules.length} failed of{' '}
                {selected.rule_checks.length})
              </h3>
              <table className="legal-table">
                <tbody>
                  {selected.rule_checks.map((r) => (
                    <tr key={r.id}>
                      <td className="nowrap">
                        <span
                          className={`legal-badge ${r.status === 'fail' ? 'risk-high' : r.status === 'pass' ? 'risk-low' : 'neutral'}`}
                        >
                          {r.status === 'fail' ? (
                            <XCircle size={12} />
                          ) : r.status === 'pass' ? (
                            <CheckCircle size={12} />
                          ) : (
                            <Info size={12} />
                          )}
                          {r.status === 'not_applicable' ? 'N/A' : humanize(r.status)}
                        </span>
                      </td>
                      <td>
                        <strong>{r.title}</strong>
                        <div className="legal-muted small">{r.detail}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {review?.checklist && review.checklist.length > 0 && (
            <div className="upload-card">
              <h3 className="legal-card-title">
                <ClipboardCheck size={16} /> {selected.standard} checklist
              </h3>
              <table className="legal-table">
                <tbody>
                  {review.checklist.map((c, i) => (
                    <tr key={i}>
                      <td className="nowrap">
                        <span
                          className={`legal-badge ${c.status === 'fail' ? 'risk-high' : c.status === 'pass' ? 'risk-low' : 'neutral'}`}
                        >
                          {humanize(c.status)}
                        </span>
                      </td>
                      <td>
                        {c.item}
                        {c.note && <div className="legal-muted small">{c.note}</div>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {selected.extraction && (
            <div className="upload-card">
              <h3 className="legal-card-title">
                <FileText size={16} /> Extracted drawing data
              </h3>
              {extraction.drawing_type && (
                <p className="legal-muted small">Type: {extraction.drawing_type}</p>
              )}
              <h4 className="eng-subhead">Title block</h4>
              <dl className="legal-fields">
                {titleBlock.map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt>{humanize(key)}</dt>
                    <dd className={value ? '' : 'eng-missing'}>{value ? asText(value) : 'missing'}</dd>
                  </React.Fragment>
                ))}
              </dl>
              {(extraction.dimensions?.length ?? 0) > 0 && (
                <>
                  <h4 className="eng-subhead">Dimensions ({extraction.dimensions.length})</h4>
                  <div className="legal-table-wrap">
                    <table className="legal-table">
                      <thead>
                        <tr>
                          <th>Value</th>
                          <th>Feature</th>
                          <th>Tolerance</th>
                          <th>View</th>
                        </tr>
                      </thead>
                      <tbody>
                        {extraction.dimensions.map((d, i) => (
                          <tr key={i}>
                            <td className="nowrap">{asText(d.value)}</td>
                            <td>{asText(d.feature)}</td>
                            <td>{asText(d.tolerance)}</td>
                            <td>{asText(d.view)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
              {(extraction.gdt?.length ?? 0) > 0 && (
                <>
                  <h4 className="eng-subhead">GD&amp;T</h4>
                  <ul className="legal-bullets">
                    {extraction.gdt.map((g, i) => (
                      <li key={i}>
                        <code>{g.frame}</code> — {g.feature}
                      </li>
                    ))}
                  </ul>
                  <p className="legal-muted small">
                    Datums defined:{' '}
                    {(extraction.datum_features || []).map((d) => d.letter).join(', ') || 'none'}
                    {(extraction.unverified_datum_claims?.length ?? 0) > 0 &&
                      ` · Rejected on verification: ${extraction.unverified_datum_claims.map((d) => d.letter).join(', ')}`}
                  </p>
                </>
              )}
              {(extraction.notes?.length ?? 0) > 0 && (
                <>
                  <h4 className="eng-subhead">Notes</h4>
                  <ul className="legal-bullets">
                    {extraction.notes.map((n, i) => (
                      <li key={i}>{asText(n)}</li>
                    ))}
                  </ul>
                </>
              )}
              {(extraction.revision_table?.length ?? 0) > 0 && (
                <>
                  <h4 className="eng-subhead">Revision table</h4>
                  <table className="legal-table">
                    <thead>
                      <tr>
                        <th>Rev</th>
                        <th>Description</th>
                        <th>Date</th>
                        <th>Approved</th>
                      </tr>
                    </thead>
                    <tbody>
                      {extraction.revision_table.map((r, i) => (
                        <tr key={i}>
                          <td>{r.revision}</td>
                          <td>{r.description}</td>
                          <td>{r.date || '—'}</td>
                          <td>{r.approved_by || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };
  const renderReview = () => (
    <>
      <div className="upload-card">
        <h2 className="upload-title">
          <Upload size={20} /> Review a drawing
        </h2>
        <p className="legal-muted">
          Upload a technical drawing. The agent renders every sheet, reads the exact text layer (or CAD
          entities for DXF), extracts the title block, dimensions, tolerances, GD&amp;T and notes, verifies
          datum symbols, runs automated rule checks and a cross-view consistency check, then performs a
          standards-based review.
        </p>
        <div className="legal-upload-actions">
          <label className="legal-muted small">
            Standard{' '}
            <select value={standard} onChange={(e) => setStandard(e.target.value)} className="eng-select">
              <option value="ISO">ISO (128 / 129-1 / 1101 / 7200)</option>
              <option value="ASME">ASME (Y14.5 / Y14.100)</option>
            </select>
          </label>
          <button
            className="upload-button"
            onClick={() => drawingInputRef.current?.click()}
            disabled={isReviewing}
          >
            {isReviewing ? <Loader2 size={16} className="spin" /> : <Upload size={16} />}
            {isReviewing ? 'Reviewing…' : 'Upload & review'}
          </button>
          <span className="legal-muted small">PDF, DXF, PNG, JPG, TIFF</span>
        </div>
        <input
          ref={drawingInputRef}
          type="file"
          accept={ACCEPTED}
          className="file-input"
          onChange={(e) => uploadDrawing(e.target.files)}
        />
        {isReviewing && (
          <p className="legal-note">
            <Loader2 size={14} className="spin" /> Reading sheets, extracting data, checking and reviewing.
            This usually takes 30–60 seconds.
          </p>
        )}
      </div>
      {renderLibrary()}
      {renderDrawingDetail()}
    </>
  );
  const renderCompare = () => (
    <>
      <div className="upload-card">
        <h2 className="upload-title">
          <GitCompare size={20} /> Compare drawings or revisions
        </h2>
        <p className="legal-muted">
          Pick a baseline (A) and a new version (B). The agent lists every change, audits each substantive
          change against the new revision-table entries, and flags inconsistencies.
        </p>
        <div className="legal-filters">
          <label className="legal-muted small">
            A (baseline){' '}
            <select value={compareA} onChange={(e) => setCompareA(e.target.value)} className="eng-select">
              <option value="">Select drawing</option>
              {reviewedDrawings.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                  {d.revision ? ` (rev ${d.revision})` : ''}
                </option>
              ))}
            </select>
          </label>
          <label className="legal-muted small">
            B (new){' '}
            <select value={compareB} onChange={(e) => setCompareB(e.target.value)} className="eng-select">
              <option value="">Select drawing</option>
              {reviewedDrawings.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                  {d.revision ? ` (rev ${d.revision})` : ''}
                </option>
              ))}
            </select>
          </label>
          <button
            className="upload-button"
            onClick={runComparison}
            disabled={!compareA || !compareB || compareA === compareB || isComparing}
          >
            {isComparing ? <Loader2 size={16} className="spin" /> : <GitCompare size={16} />}
            {isComparing ? 'Comparing…' : 'Compare'}
          </button>
        </div>
        {reviewedDrawings.length < 2 && (
          <p className="legal-muted small">Review at least two drawings first.</p>
        )}
      </div>

      {comparison && (
        <>
          <div className="upload-card">
            <h3 className="legal-card-title">Summary</h3>
            <p className="legal-prose">{comparison.summary}</p>
            <p className="legal-muted small">
              {comparison.a.filename} → {comparison.b.filename} · {humanize(comparison.relationship)}
            </p>
          </div>

          <div className="upload-card">
            <h3 className="legal-card-title">
              <ClipboardCheck size={16} /> Revision control
            </h3>
            <div className="legal-drawer-actions">
              <span
                className={`legal-badge ${comparison.revision_control.revision_incremented ? 'risk-low' : comparison.revision_control.revision_incremented === false ? 'risk-high' : 'neutral'}`}
              >
                {comparison.revision_control.revision_incremented ? (
                  <CheckCircle size={12} />
                ) : (
                  <XCircle size={12} />
                )}
                Revision{' '}
                {comparison.revision_control.revision_incremented
                  ? 'incremented'
                  : comparison.revision_control.revision_incremented === false
                    ? 'not incremented'
                    : 'unknown'}
              </span>
              <span
                className={`legal-badge ${comparison.revision_control.changes_recorded_in_revision_table ? 'risk-low' : comparison.revision_control.changes_recorded_in_revision_table === false ? 'risk-high' : 'neutral'}`}
              >
                {comparison.revision_control.changes_recorded_in_revision_table ? (
                  <CheckCircle size={12} />
                ) : (
                  <XCircle size={12} />
                )}
                {comparison.revision_control.changes_recorded_in_revision_table
                  ? 'All changes recorded'
                  : comparison.revision_control.changes_recorded_in_revision_table === false
                    ? 'Unrecorded changes'
                    : 'No substantive changes'}
              </span>
            </div>
            <p className="legal-prose">{comparison.revision_control.comment}</p>
            {comparison.revision_control.unrecorded_changes.length > 0 && (
              <ul className="legal-bullets">
                {comparison.revision_control.unrecorded_changes.map((c, i) => (
                  <li key={i}>
                    <strong>Not in revision table:</strong> {asText(c)}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="upload-card">
            <h3 className="legal-card-title">Changes ({comparison.changes.length})</h3>
            <div className="legal-table-wrap">
              <table className="legal-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>A</th>
                    <th>B</th>
                    <th>Type</th>
                    <th>Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.changes.map((c, i) => (
                    <tr key={i}>
                      <td>{asText(c.item)}</td>
                      <td>{asText(c.a)}</td>
                      <td>{asText(c.b)}</td>
                      <td>{humanize(c.change_type)}</td>
                      <td>
                        <span
                          className={`legal-badge ${c.significance === 'high' ? 'risk-high' : c.significance === 'medium' ? 'risk-medium' : 'neutral'}`}
                        >
                          {humanize(c.impact)} · {c.significance}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {comparison.inconsistencies.length > 0 && (
              <>
                <h4 className="eng-subhead">Inconsistencies</h4>
                <ul className="legal-bullets">
                  {comparison.inconsistencies.map((x, i) => (
                    <li key={i}>
                      {asText(x.description)}{' '}
                      <span className="legal-muted small">— {asText(x.recommendation)}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <p className="legal-muted small">
              <strong>Recommendation:</strong> {comparison.recommendation}
            </p>
            <button className="upload-button" onClick={draftEcnFromComparison}>
              <FileText size={16} /> Draft an ECN from this comparison
            </button>
          </div>
        </>
      )}
    </>
  );
  const renderTemplateEditor = () => {
    if (!draft)
      return (
        <div className="upload-card">
          <p className="legal-empty-note">
            Select a template to edit, create a new one, or import one from a file.
          </p>
        </div>
      );
    return (
      <div className="upload-card">
        <div className="eng-editor-header">
          <input
            className="eng-title-input"
            value={draft.name}
            onChange={(e) =>
              updateDraft((t) => {
                t.name = e.target.value;
              })
            }
            aria-label="Template name"
          />
          {draft.builtin && <span className="legal-badge neutral">Built-in · saving creates a copy</span>}
        </div>
        <textarea
          className="legal-textarea"
          rows={2}
          value={draft.description}
          placeholder="Description"
          onChange={(e) =>
            updateDraft((t) => {
              t.description = e.target.value;
            })
          }
        />
        <div className="legal-filters">
          <button className="upload-button" onClick={saveTemplate} disabled={templateBusy !== null}>
            {templateBusy === 'save' ? <Loader2 size={16} className="spin" /> : <Save size={16} />} Save
          </button>
          <button
            className="upload-button secondary"
            onClick={reviewTemplate}
            disabled={!draft.id || templateBusy !== null}
            title={draft.id ? '' : 'Save the template first'}
          >
            {templateBusy === 'review' ? <Loader2 size={16} className="spin" /> : <Sparkles size={16} />} AI
            review
          </button>
          {draft.id && !draft.builtin && (
            <button className="action-button delete" onClick={deleteTemplate}>
              <Trash2 size={14} /> Delete
            </button>
          )}
        </div>

        {templateReview && (
          <div className="eng-suggestions">
            <h4 className="eng-subhead">
              <Sparkles size={14} /> AI review
            </h4>
            <p className="legal-prose">{templateReview.assessment}</p>
            <ul className="legal-bullets">
              {templateReview.suggestions.map((s, i) => (
                <li key={i}>
                  <span
                    className={`legal-badge ${s.priority === 'high' ? 'risk-high' : s.priority === 'medium' ? 'risk-medium' : 'neutral'}`}
                  >
                    {s.priority}
                  </span>{' '}
                  <strong>
                    {humanize(s.type)} · {s.target}:
                  </strong>{' '}
                  {s.detail}
                </li>
              ))}
            </ul>
            <button className="upload-button" onClick={applyRevisedTemplate}>
              <CheckCircle size={16} /> Apply revised template (review, then Save)
            </button>
          </div>
        )}

        {draft.sections.map((section, si) => (
          <div key={si} className="eng-section">
            <div className="eng-section-header">
              <input
                className="eng-section-title"
                value={section.title}
                aria-label="Section title"
                onChange={(e) =>
                  updateDraft((t) => {
                    t.sections[si].title = e.target.value;
                  })
                }
              />
              <button
                className="theme-toggle"
                disabled={si === 0}
                aria-label="Move section up"
                onClick={() =>
                  updateDraft((t) => {
                    [t.sections[si - 1], t.sections[si]] = [t.sections[si], t.sections[si - 1]];
                  })
                }
              >
                <ArrowUp size={14} />
              </button>
              <button
                className="theme-toggle"
                disabled={si === draft.sections.length - 1}
                aria-label="Move section down"
                onClick={() =>
                  updateDraft((t) => {
                    [t.sections[si + 1], t.sections[si]] = [t.sections[si], t.sections[si + 1]];
                  })
                }
              >
                <ArrowDown size={14} />
              </button>
              <button
                className="theme-toggle"
                aria-label="Delete section"
                onClick={() =>
                  updateDraft((t) => {
                    t.sections.splice(si, 1);
                  })
                }
              >
                <Trash2 size={14} />
              </button>
            </div>
            <textarea
              className="legal-textarea eng-guidance"
              rows={2}
              value={section.guidance}
              placeholder="Guidance for whoever fills this section"
              onChange={(e) =>
                updateDraft((t) => {
                  t.sections[si].guidance = e.target.value;
                })
              }
            />
            {section.fields.map((field, fi) => (
              <div key={fi} className="eng-field-row">
                <input
                  value={field.name}
                  aria-label="Field name"
                  onChange={(e) =>
                    updateDraft((t) => {
                      t.sections[si].fields[fi].name = e.target.value;
                    })
                  }
                />
                <select
                  value={field.type}
                  aria-label="Field type"
                  onChange={(e) =>
                    updateDraft((t) => {
                      t.sections[si].fields[fi].type = e.target.value;
                    })
                  }
                >
                  <option value="text">Text</option>
                  <option value="longtext">Long text</option>
                  <option value="date">Date</option>
                  <option value="table">Table</option>
                </select>
                <label className="legal-muted small eng-required">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(e) =>
                      updateDraft((t) => {
                        t.sections[si].fields[fi].required = e.target.checked;
                      })
                    }
                  />{' '}
                  Required
                </label>
                <button
                  className="theme-toggle"
                  aria-label="Delete field"
                  onClick={() =>
                    updateDraft((t) => {
                      t.sections[si].fields.splice(fi, 1);
                    })
                  }
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
            <button
              className="legal-link"
              onClick={() =>
                updateDraft((t) => {
                  t.sections[si].fields.push({ name: 'New field', type: 'text', required: false });
                })
              }
            >
              <Plus size={14} /> Add field
            </button>
          </div>
        ))}
        <button
          className="action-button update"
          onClick={() =>
            updateDraft((t) => {
              t.sections.push({ title: 'New section', guidance: '', fields: [] });
            })
          }
        >
          <Plus size={14} /> Add section
        </button>
      </div>
    );
  };
  const renderTemplates = () => (
    <div className="eng-two-col">
      <div className="upload-card">
        <h3 className="legal-card-title">
          <LayoutTemplate size={16} /> Templates
        </h3>
        <div className="legal-filters">
          <button
            className="action-button update"
            onClick={() => {
              setDraft(emptyTemplate());
              setTemplateReview(null);
            }}
          >
            <Plus size={14} /> New
          </button>
          <button
            className="action-button update"
            onClick={() => templateInputRef.current?.click()}
            disabled={templateBusy !== null}
          >
            {templateBusy === 'import' ? <Loader2 size={14} className="spin" /> : <Upload size={14} />} Import
            file
          </button>
        </div>
        <input
          ref={templateInputRef}
          type="file"
          accept=".docx,.pdf,.txt,.md"
          className="file-input"
          onChange={(e) => importTemplate(e.target.files)}
        />
        <ul className="eng-template-list">
          {templates.map((t) => (
            <li key={t.id}>
              <button
                className={`eng-template-button ${draft?.id === t.id ? 'active' : ''}`}
                onClick={() => editTemplate(t)}
              >
                <span className="legal-doc-title">{t.name}</span>
                <span className="legal-muted small">
                  {t.builtin ? 'Built-in' : 'Custom'} · {t.sections.length} sections
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      {renderTemplateEditor()}
    </div>
  );
  const renderDocuments = () => (
    <>
      <div className="upload-card">
        <h2 className="upload-title">
          <FileText size={20} /> Generate documentation
        </h2>
        <p className="legal-muted">
          Fill a template from reviewed drawings and comparisons. Facts are copied from the sources; anything
          the sources do not contain is left empty and flagged, drafted analysis is marked [DRAFT], and
          numbers not found in the sources are flagged.
        </p>
        <div className="eng-generate-grid">
          <label className="legal-muted small">
            Template
            <select
              value={generateTemplate}
              onChange={(e) => setGenerateTemplate(e.target.value)}
              className="eng-select"
            >
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <div>
            <div className="legal-muted small">Source drawings</div>
            <div className="eng-checklist">
              {reviewedDrawings.length === 0 && (
                <span className="legal-muted small">No reviewed drawings yet</span>
              )}
              {reviewedDrawings.map((d) => (
                <label key={d.id}>
                  <input
                    type="checkbox"
                    checked={generateDrawings.includes(d.id)}
                    onChange={() => setGenerateDrawings(toggle(generateDrawings, d.id))}
                  />{' '}
                  {d.filename}
                </label>
              ))}
            </div>
          </div>
          <div>
            <div className="legal-muted small">Source comparisons</div>
            <div className="eng-checklist">
              {comparisons.length === 0 && <span className="legal-muted small">No comparisons yet</span>}
              {comparisons.map((c) => (
                <label key={c.id}>
                  <input
                    type="checkbox"
                    checked={generateComparisons.includes(c.id)}
                    onChange={() => setGenerateComparisons(toggle(generateComparisons, c.id))}
                  />{' '}
                  {c.result.a.filename} → {c.result.b.filename}{' '}
                  <span className="legal-muted small">· {new Date(c.created_at).toLocaleString()}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <textarea
          className="legal-textarea"
          rows={2}
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Extra facts or instructions, e.g. ECN number ECN-0042, originator, reason for change"
        />
        <div className="legal-filters">
          <button
            className="upload-button"
            onClick={generateDocument}
            disabled={isGenerating || (generateDrawings.length === 0 && generateComparisons.length === 0)}
          >
            {isGenerating ? <Loader2 size={16} className="spin" /> : <Sparkles size={16} />}{' '}
            {isGenerating ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </div>

      <div className="eng-two-col">
        <div className="upload-card">
          <h3 className="legal-card-title">
            <FileText size={16} /> Documents ({documents.length})
          </h3>
          <ul className="eng-template-list">
            {documents.map((d) => (
              <li key={d.id}>
                <button
                  className={`eng-template-button ${openDocument?.id === d.id ? 'active' : ''}`}
                  onClick={() => loadDocument(d.id)}
                >
                  <span className="legal-doc-title">{d.title}</span>
                  <span className="legal-muted small">{d.template_name}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        {openDocument ? (
          <div className="upload-card">
            <div className="eng-editor-header">
              <input
                className="eng-title-input"
                value={openDocument.title}
                aria-label="Document title"
                onChange={(e) => {
                  setOpenDocument({ ...openDocument, title: e.target.value });
                  setDocumentSaved(false);
                }}
              />
            </div>
            <div className="legal-filters">
              <button className="upload-button" onClick={saveDocument} disabled={documentSaved}>
                <Save size={16} /> {documentSaved ? 'Saved' : 'Save'}
              </button>
              <a
                className="action-button update"
                href={`${API_BASE}/engineering/documents/${openDocument.id}/export?format=docx`}
              >
                <Download size={14} /> Word
              </a>
              <a
                className="action-button update"
                href={`${API_BASE}/engineering/documents/${openDocument.id}/export?format=md`}
              >
                <Download size={14} /> Markdown
              </a>
              <button
                className="action-button update"
                onClick={async () => {
                  const text = await (
                    await fetch(`${API_BASE}/engineering/documents/${openDocument.id}/export?format=md`, { credentials: "include" })
                  ).text();
                  navigator.clipboard.writeText(text);
                }}
              >
                <Copy size={14} /> Copy
              </button>
              <button className="action-button delete" onClick={deleteDocument}>
                <Trash2 size={14} /> Delete
              </button>
            </div>
            {!documentSaved && <p className="legal-muted small">Unsaved edits. Save before exporting.</p>}

            {openDocument.missing_information.length > 0 && (
              <div className="legal-note eng-missing-box">
                <AlertTriangle size={16} />
                <div>
                  <strong>{openDocument.missing_information.length} item(s) need attention</strong>
                  <ul className="legal-bullets">
                    {openDocument.missing_information.map((m, i) => (
                      <li key={i}>
                        <strong>
                          {m.section} / {m.field}:
                        </strong>{' '}
                        {m.reason}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {openDocument.sections.map((section, si) => (
              <div key={si} className="eng-section">
                <h4 className="eng-subhead">{section.title}</h4>
                {Object.entries(section.fields).map(([name, value]) => {
                  const type = templateFieldType(section.title, name);
                  const flagged = openDocument.missing_information.some(
                    (m) => m.section === section.title && m.field === name,
                  );
                  return (
                    <label key={name} className="eng-doc-field">
                      <span className="legal-muted small">
                        {name}
                        {flagged && <AlertTriangle size={12} className="eng-flag" />}
                      </span>
                      {type === 'longtext' || type === 'table' ? (
                        <textarea
                          className={`legal-textarea ${type === 'table' ? 'eng-mono' : ''} ${flagged ? 'eng-flagged' : ''}`}
                          rows={
                            type === 'table' ? Math.min(Math.max(value.split('\n').length + 1, 3), 14) : 3
                          }
                          value={value}
                          onChange={(e) => editDocumentField(si, name, e.target.value)}
                        />
                      ) : (
                        <input
                          className={flagged ? 'eng-flagged' : ''}
                          value={value}
                          onChange={(e) => editDocumentField(si, name, e.target.value)}
                        />
                      )}
                    </label>
                  );
                })}
                {section.notes && <p className="legal-muted small">{section.notes}</p>}
              </div>
            ))}
          </div>
        ) : (
          <div className="upload-card">
            <p className="legal-empty-note">Generate a document or open one from the list.</p>
          </div>
        )}
      </div>
    </>
  );
  return (
    <div className="upload-container">
      <div className="upload-content legal-content">
        <div className="legal-header">
          <div>
            <h2 className="legal-page-title">
              <Ruler size={22} /> Engineering
            </h2>
            <p className="legal-muted">
              AI agent for drawing review, change control and technical documentation.
            </p>
          </div>
          <nav className="legal-subnav" aria-label="Engineering views">
            {[
              { id: 'review', label: 'Review', icon: ClipboardCheck },
              { id: 'compare', label: 'Compare', icon: GitCompare },
              { id: 'templates', label: 'Templates', icon: LayoutTemplate },
              { id: 'documents', label: 'Documents', icon: FileText },
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

        {view === 'review' && renderReview()}
        {view === 'compare' && renderCompare()}
        {view === 'templates' && renderTemplates()}
        {view === 'documents' && renderDocuments()}

        <p className="legal-disclaimer">
          AI-assisted checking supports, and does not replace, a qualified engineer’s review and approval.
        </p>
      </div>
    </div>
  );
};
export default EngineeringWorkspace;
