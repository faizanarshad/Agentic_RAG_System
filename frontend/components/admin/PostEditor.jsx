'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Bold, Code, ExternalLink, Heading2, ImagePlus, Italic, Link2, List, ListOrdered, Loader2, Quote, Save, Trash2, Upload,
} from 'lucide-react';
import { API_BASE, fetchBackend, jsonRequest } from '@/lib/api';
import { site } from '@/lib/site';
import { TimeSeriesChart } from './charts';
import { postState } from './PostsPage';

const EMPTY = {
  title: '', slug: '', excerpt: '', content_md: '', cover_image: null, cover_alt: '', tags: [],
  status: 'draft', seo_title: '', seo_description: '', published_at: null,
};

const slugify = (v) => v.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);

// <input type="datetime-local"> works in local time; the API stores UTC ISO strings
const toLocalInput = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};
const fromLocalInput = (value) => (value ? new Date(value).toISOString() : null);

const SAVED_MESSAGES = {
  published: 'Published. The public page updates within a minute.',
  scheduled: 'Scheduled.',
  draft: 'Draft saved.',
};

function Counter({ value, max }) {
  return <span className={`editor-counter ${value.length > max ? 'over' : ''}`}>{value.length}/{max}</span>;
}

export default function PostEditor({ postId }) {
  const router = useRouter();
  const savedFlag = useSearchParams().get('saved');
  const textareaRef = useRef(null);
  const [post, setPost] = useState(EMPTY);
  const [tagsText, setTagsText] = useState('');
  const [slugTouched, setSlugTouched] = useState(false);
  const [loading, setLoading] = useState(Boolean(postId));
  const [mode, setMode] = useState('write');
  const [previewHtml, setPreviewHtml] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  // A new post navigates to its permanent URL after the first save; the flag carries the confirmation over
  const [message, setMessage] = useState(SAVED_MESSAGES[savedFlag] ? { ok: true, text: SAVED_MESSAGES[savedFlag] } : null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!postId) return;
    fetchBackend(`/admin/posts/${postId}`)
      .then((p) => {
        setPost({ ...EMPTY, ...p, cover_alt: p.cover_alt || '', seo_title: p.seo_title || '', seo_description: p.seo_description || '' });
        setTagsText(p.tags.join(', '));
        setSlugTouched(true);
      })
      .catch((e) => setMessage({ ok: false, text: e.message }))
      .finally(() => setLoading(false));
    fetchBackend(`/admin/posts/${postId}/stats`).then(setStats).catch(() => {});
  }, [postId]);

  const set = (field, value) => setPost((p) => ({ ...p, [field]: value }));

  const onTitle = (value) => {
    setPost((p) => ({ ...p, title: value, slug: slugTouched ? p.slug : slugify(value) }));
  };

  const showPreview = async () => {
    setMode('preview');
    try {
      setPreviewHtml((await fetchBackend('/admin/posts/preview', jsonRequest('POST', { content_md: post.content_md }))).html);
    } catch (e) {
      setPreviewHtml(`<p>Preview failed: ${e.message.replace(/</g, '&lt;')}</p>`);
    }
  };

  // Wrap or prefix the selection in the Markdown textarea
  const format = (before, after = '', placeholder = 'text', linePrefix = false) => {
    const el = textareaRef.current;
    if (!el) return;
    const { selectionStart: start, selectionEnd: end, value } = el;
    const selected = value.slice(start, end) || placeholder;
    let insert;
    if (linePrefix) {
      insert = selected.split('\n').map((line, i) => (typeof before === 'function' ? before(i) : before) + line).join('\n');
    } else {
      insert = before + selected + after;
    }
    const next = value.slice(0, start) + insert + value.slice(end);
    set('content_md', next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start, start + insert.length);
    });
  };

  const uploadImage = async (file, target) => {
    if (!file) return;
    setUploading(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const result = await fetchBackend('/admin/uploads', { method: 'POST', body: form });
      if (target === 'cover') {
        set('cover_image', result.name);
      } else {
        format(`![${file.name.replace(/\.[^.]+$/, '')}](${API_BASE}${result.url})`, '', '', false);
      }
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setUploading(false);
    }
  };

  const save = async (statusOverride) => {
    setSaving(true);
    setMessage(null);
    const body = {
      ...post,
      status: statusOverride || post.status,
      tags: tagsText.split(',').map((t) => t.trim()).filter(Boolean),
      slug: post.slug || slugify(post.title),
    };
    try {
      const saved = postId
        ? await fetchBackend(`/admin/posts/${postId}`, jsonRequest('PUT', body))
        : await fetchBackend('/admin/posts', jsonRequest('POST', body));
      setPost({ ...EMPTY, ...saved, cover_alt: saved.cover_alt || '', seo_title: saved.seo_title || '', seo_description: saved.seo_description || '' });
      const outcome = saved.status === 'published' ? postState(saved) : 'draft';
      setMessage({ ok: true, text: SAVED_MESSAGES[outcome] });
      if (!postId) router.replace(`/admin/posts/${saved.id}?saved=${outcome}`);
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm('Delete this post? This cannot be undone.')) return;
    await fetchBackend(`/admin/posts/${postId}`, { method: 'DELETE' });
    router.replace('/admin/posts');
  };

  if (loading) return <div className="ws-loading">Loading post…</div>;

  const state = postState(post);
  const seoTitle = post.seo_title || post.title || 'Post title';
  const seoDescription = post.seo_description || post.excerpt || 'Add an excerpt or meta description.';

  return (
    <div className="editor">
      <div className="editor__main">
        <section className="upload-card">
          <label className="editor-field editor-title">
            <span className="visually-hidden">Title</span>
            <input value={post.title} onChange={(e) => onTitle(e.target.value)} placeholder="Post title" maxLength={160} />
          </label>
          <label className="editor-field" style={{ marginTop: 12 }}>
            <span>Excerpt <Counter value={post.excerpt} max={320} /></span>
            <textarea rows={2} value={post.excerpt} onChange={(e) => set('excerpt', e.target.value)}
              placeholder="One or two sentences shown on the blog list and in search results" />
          </label>
        </section>

        <section className="upload-card">
          <div className="md-toolbar" role="toolbar" aria-label="Formatting">
            <button type="button" onClick={() => format('## ', '', 'Heading', true)} aria-label="Heading"><Heading2 size={16} /></button>
            <button type="button" onClick={() => format('**', '**')} aria-label="Bold"><Bold size={16} /></button>
            <button type="button" onClick={() => format('*', '*')} aria-label="Italic"><Italic size={16} /></button>
            <button type="button" onClick={() => format('[', '](https://)', 'link text')} aria-label="Link"><Link2 size={16} /></button>
            <button type="button" onClick={() => format('- ', '', 'List item', true)} aria-label="Bulleted list"><List size={16} /></button>
            <button type="button" onClick={() => format((i) => `${i + 1}. `, '', 'List item', true)} aria-label="Numbered list"><ListOrdered size={16} /></button>
            <button type="button" onClick={() => format('> ', '', 'Quote', true)} aria-label="Quote"><Quote size={16} /></button>
            <button type="button" onClick={() => format('```\n', '\n```', 'code')} aria-label="Code block"><Code size={16} /></button>
            <label className="md-upload" aria-label="Insert image" title="Insert image">
              <ImagePlus size={16} />
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden onChange={(e) => uploadImage(e.target.files[0], 'inline')} />
            </label>
            <div className="md-tabs">
              <button type="button" aria-pressed={mode === 'write'} onClick={() => setMode('write')}>Write</button>
              <button type="button" aria-pressed={mode === 'preview'} onClick={showPreview}>Preview</button>
            </div>
          </div>
          {mode === 'write' ? (
            <textarea ref={textareaRef} className="md-editor" value={post.content_md} aria-label="Post content (Markdown)"
              onChange={(e) => set('content_md', e.target.value)}
              placeholder={'Write in Markdown.\n\n## A section heading\n\nParagraphs, **bold**, lists, links, images, tables and code blocks are supported.'} />
          ) : (
            // Preview HTML comes from the same server-side renderer and sanitiser used for publishing
            <div className="md-preview" dangerouslySetInnerHTML={{ __html: previewHtml || '<p><em>Nothing to preview.</em></p>' }} />
          )}
        </section>

        {stats && (
          <section className="upload-card">
            <h3 className="legal-card-title">Views (last 30 days) · {stats.views} total, {stats.visitors} visitors</h3>
            <TimeSeriesChart series={stats.series} label="Post views" />
          </section>
        )}
      </div>

      <aside className="editor__side">
        <section className="upload-card">
          <h3 className="legal-card-title">Publish <span className={`status-pill status-pill--${state}`}>{state}</span></h3>
          <label className="editor-field">
            <span>Publish date <em className="admin-note">(future date = scheduled)</em></span>
            <input type="datetime-local" value={toLocalInput(post.published_at)} onChange={(e) => set('published_at', fromLocalInput(e.target.value))} />
          </label>
          {message && <p className={`form-msg ${message.ok ? 'ok' : 'err'}`} role="status" style={{ marginTop: 12 }}>{message.text}</p>}
          <div className="admin-actions" style={{ marginTop: 14 }}>
            <button className="upload-button" disabled={saving || !post.title.trim()} onClick={() => save('published')}>
              {saving ? <Loader2 size={16} className="spin" /> : <Upload size={16} />}
              {post.status === 'published' ? 'Update' : post.published_at && new Date(post.published_at) > new Date() ? 'Schedule' : 'Publish'}
            </button>
            <button className="action-button update" disabled={saving || !post.title.trim()} onClick={() => save('draft')}>
              <Save size={14} /> {post.status === 'published' ? 'Unpublish' : 'Save draft'}
            </button>
          </div>
          <div className="admin-actions" style={{ marginTop: 10 }}>
            {state === 'published' && (
              <a className="action-button update" href={`/blog/${post.slug}`} target="_blank" rel="noreferrer"><ExternalLink size={14} /> View live</a>
            )}
            {postId && <button className="action-button delete" onClick={remove}><Trash2 size={14} /> Delete</button>}
          </div>
        </section>

        <section className="upload-card">
          <h3 className="legal-card-title">Details</h3>
          <label className="editor-field">
            <span>URL slug</span>
            <input value={post.slug} onChange={(e) => { setSlugTouched(true); set('slug', slugify(e.target.value)); }} placeholder="auto from title" />
          </label>
          <label className="editor-field" style={{ marginTop: 12 }}>
            <span>Tags <em className="admin-note">(comma-separated, up to 8)</em></span>
            <input value={tagsText} onChange={(e) => setTagsText(e.target.value)} placeholder="engineering, gd&t" />
          </label>
        </section>

        <section className="upload-card">
          <h3 className="legal-card-title">Cover image</h3>
          {post.cover_image ? (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="cover-preview" src={`${API_BASE}/public/uploads/${post.cover_image}`} alt={post.cover_alt || 'Cover preview'} />
              <label className="editor-field" style={{ marginTop: 10 }}>
                <span>Alt text</span>
                <input value={post.cover_alt} onChange={(e) => set('cover_alt', e.target.value)} placeholder="Describe the image" />
              </label>
              <button className="legal-link" style={{ marginTop: 8 }} onClick={() => set('cover_image', null)}>Remove cover</button>
            </>
          ) : (
            <label className="action-button update" style={{ cursor: 'pointer' }}>
              {uploading ? <Loader2 size={14} className="spin" /> : <ImagePlus size={14} />} Upload cover
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden onChange={(e) => uploadImage(e.target.files[0], 'cover')} />
            </label>
          )}
          <p className="admin-note" style={{ marginTop: 8 }}>Images are resized to 2000 px and converted to WebP. Recommended 1200 × 630.</p>
        </section>

        <section className="upload-card">
          <h3 className="legal-card-title">Search appearance</h3>
          <label className="editor-field">
            <span>SEO title <Counter value={post.seo_title} max={60} /></span>
            <input value={post.seo_title} onChange={(e) => set('seo_title', e.target.value)} placeholder={post.title} maxLength={70} />
          </label>
          <label className="editor-field" style={{ marginTop: 12 }}>
            <span>Meta description <Counter value={post.seo_description} max={155} /></span>
            <textarea rows={3} value={post.seo_description} onChange={(e) => set('seo_description', e.target.value)} placeholder={post.excerpt} maxLength={170} />
          </label>
          <div className="serp" style={{ marginTop: 12 }} aria-label="Search result preview">
            <span className="serp__url">{site.url.replace(/^https?:\/\//, '')} › blog › {post.slug || 'post-slug'}</span>
            <span className="serp__title">{seoTitle.length > 60 ? `${seoTitle.slice(0, 57)}…` : seoTitle}</span>
            <span className="serp__desc">{seoDescription.length > 155 ? `${seoDescription.slice(0, 152)}…` : seoDescription}</span>
          </div>
        </section>
      </aside>
    </div>
  );
}
