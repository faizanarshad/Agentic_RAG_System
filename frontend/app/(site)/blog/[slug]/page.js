import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Breadcrumbs from '@/components/site/Breadcrumbs';
import JsonLd from '@/components/site/JsonLd';
import PostCard, { formatDate } from '@/components/site/PostCard';
import { getPost, getPublishedPosts, uploadUrl } from '@/lib/content-api';
import { absoluteUrl, site } from '@/lib/site';

export const revalidate = 60;

// Prerender published posts at build time; new posts render on first request, then stay cached
export async function generateStaticParams() {
  const posts = await getPublishedPosts();
  return posts.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) return { title: 'Article not found', robots: { index: false } };
  const title = post.seo_title || post.title;
  const description = post.seo_description || post.excerpt;
  const path = `/blog/${post.slug}`;
  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: {
      type: 'article',
      url: path,
      title,
      description,
      publishedTime: post.published_at,
      modifiedTime: post.updated_at,
      tags: post.tags,
      ...(post.cover_image && { images: [{ url: uploadUrl(post.cover_image), alt: post.cover_alt || post.title }] }),
    },
  };
}

export default async function PostPage({ params }) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();
  const related = (await getPublishedPosts())
    .filter((p) => p.slug !== post.slug)
    .sort((a, b) => b.tags.filter((t) => post.tags.includes(t)).length - a.tags.filter((t) => post.tags.includes(t)).length)
    .slice(0, 3);

  return (
    <>
      <JsonLd
        data={{
          '@context': 'https://schema.org',
          '@type': 'BlogPosting',
          headline: post.title,
          description: post.seo_description || post.excerpt,
          datePublished: post.published_at,
          dateModified: post.updated_at,
          mainEntityOfPage: absoluteUrl(`/blog/${post.slug}`),
          author: { '@type': 'Person', name: post.author_name || site.name },
          publisher: { '@id': `${site.url}/#organization` },
          keywords: post.tags.join(', '),
          ...(post.cover_image && { image: uploadUrl(post.cover_image) }),
        }}
      />
      <article>
        <header className="section--ink blueprint page-hero">
          <div className="container page-hero__inner post-header">
            <Breadcrumbs items={[{ name: 'Blog', path: '/blog' }, { name: post.title, path: `/blog/${post.slug}` }]} />
            <p className="eyebrow">{post.tags[0] || 'Article'}</p>
            <h1 className="display post-title">{post.title}</h1>
            {post.excerpt && <p className="lede">{post.excerpt}</p>}
            <p className="post-meta">
              {post.author_name && <span>By {post.author_name}</span>}
              <time dateTime={post.published_at}>{formatDate(post.published_at)}</time>
              <span>{post.reading_minutes} min read</span>
            </p>
          </div>
        </header>
        <div className="section">
          <div className="container post-body">
            {post.cover_image && (
              <Image
                className="post-cover"
                src={uploadUrl(post.cover_image)}
                alt={post.cover_alt || ''}
                width={1200}
                height={630}
                unoptimized
                loading="eager"
                fetchPriority="high"
              />
            )}
            {/* HTML is rendered from Markdown and sanitised (allow-list) by the API when the post is saved */}
            <div className="post-content" dangerouslySetInnerHTML={{ __html: post.content_html }} />
            {post.tags.length > 0 && (
              <ul className="post-tags" aria-label="Tags">{post.tags.map((t) => <li key={t}>{t}</li>)}</ul>
            )}
            <Link className="text-link" href="/blog"><ArrowLeft size={16} aria-hidden="true" /> All articles</Link>
          </div>
        </div>
      </article>
      {related.length > 0 && (
        <section className="section section--surface" aria-labelledby="related-title">
          <div className="container">
            <h2 id="related-title" className="h2" style={{ marginBottom: 32 }}>Related articles</h2>
            <div className="grid-3">{related.map((p) => <PostCard key={p.id} post={p} />)}</div>
          </div>
        </section>
      )}
    </>
  );
}
