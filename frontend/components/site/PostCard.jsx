import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { uploadUrl } from '@/lib/content-api';

export const formatDate = (value) =>
  new Date(value).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

export default function PostCard({ post, eager = false }) {
  return (
    <article className="card card--link post-card">
      {post.cover_image && (
        <Image
          className="post-card__image"
          src={uploadUrl(post.cover_image)}
          alt={post.cover_alt || ''}
          width={800}
          height={420}
          unoptimized // already resized and encoded as WebP by the API
          loading={eager ? 'eager' : 'lazy'}
        />
      )}
      <p className="card__kicker">
        <time dateTime={post.published_at}>{formatDate(post.published_at)}</time> · {post.reading_minutes} min read
      </p>
      <h2 className="h3">{post.title}</h2>
      {post.excerpt && <p>{post.excerpt}</p>}
      {post.tags?.length > 0 && (
        <ul className="post-tags" aria-label="Tags">
          {post.tags.map((t) => <li key={t}>{t}</li>)}
        </ul>
      )}
      <Link className="text-link card__link" href={`/blog/${post.slug}`}>
        Read article <ArrowRight size={16} aria-hidden="true" />
      </Link>
    </article>
  );
}
