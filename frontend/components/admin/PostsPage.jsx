'use client';

import Link from 'next/link';
import { ExternalLink, Pencil, Plus, Trash2 } from 'lucide-react';
import { fetchBackend } from '@/lib/api';
import { AdminState, useAdminData } from './AdminFrame';

export function postState(post) {
  if (post.status !== 'published') return 'draft';
  return post.published_at && new Date(post.published_at) > new Date() ? 'scheduled' : 'published';
}

export default function PostsPage() {
  const { data, loading, error, reload } = useAdminData('/admin/posts');

  const remove = async (post) => {
    if (!window.confirm(`Delete "${post.title}"? This cannot be undone.`)) return;
    await fetchBackend(`/admin/posts/${post.id}`, { method: 'DELETE' });
    reload();
  };

  const counts = (data?.posts || []).reduce((acc, p) => ({ ...acc, [postState(p)]: (acc[postState(p)] || 0) + 1 }), {});

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">
          Posts {data && <span className="legal-muted small">· {counts.published || 0} published · {counts.scheduled || 0} scheduled · {counts.draft || 0} drafts</span>}
        </h2>
        <Link className="upload-button" href="/admin/posts/new"><Plus size={16} aria-hidden="true" /> New post</Link>
      </div>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <section className="upload-card">
          {data.posts.length === 0 ? (
            <p className="legal-empty-note">No posts yet. Create the first one to start the blog.</p>
          ) : (
            <div className="legal-table-wrap">
              <table className="legal-table admin-table">
                <thead><tr><th>Title</th><th>Status</th><th>Views (30d / all)</th><th>Published</th><th>Updated</th><th /></tr></thead>
                <tbody>
                  {data.posts.map((p) => {
                    const state = postState(p);
                    return (
                      <tr key={p.id}>
                        <td className="wrap">
                          <Link className="legal-link" href={`/admin/posts/${p.id}`}><strong>{p.title}</strong></Link>
                          <div className="legal-muted small">/blog/{p.slug}{p.tags.length ? ` · ${p.tags.join(', ')}` : ''}</div>
                        </td>
                        <td><span className={`status-pill status-pill--${state}`}>{state}</span></td>
                        <td>{p.views_30d.toLocaleString()} / {p.views.toLocaleString()}</td>
                        <td>{p.published_at ? new Date(p.published_at).toLocaleString() : '—'}</td>
                        <td>{new Date(p.updated_at).toLocaleString()}</td>
                        <td>
                          <div className="admin-actions">
                            <Link className="action-button update" href={`/admin/posts/${p.id}`}><Pencil size={14} /> Edit</Link>
                            {state === 'published' && (
                              <a className="action-button update" href={`/blog/${p.slug}`} target="_blank" rel="noreferrer"><ExternalLink size={14} /> View</a>
                            )}
                            <button className="action-button delete" onClick={() => remove(p)} aria-label={`Delete ${p.title}`}><Trash2 size={14} /></button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}
