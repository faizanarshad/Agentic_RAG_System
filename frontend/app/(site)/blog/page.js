import Breadcrumbs from '@/components/site/Breadcrumbs';
import JsonLd from '@/components/site/JsonLd';
import PostCard from '@/components/site/PostCard';
import { getPublishedPosts } from '@/lib/content-api';
import { absoluteUrl, site } from '@/lib/site';

const description = 'Insights on AI document review, engineering drawing checks, legal document synthesis and verifiable AI.';

export const revalidate = 60;

export const metadata = {
  title: 'Blog',
  description,
  alternates: { canonical: '/blog' },
  openGraph: { url: '/blog', title: `Blog | ${site.name}`, description },
};

export default async function BlogPage() {
  const posts = await getPublishedPosts();
  return (
    <>
      <JsonLd
        data={{
          '@context': 'https://schema.org',
          '@type': 'Blog',
          name: `${site.name} Blog`,
          url: absoluteUrl('/blog'),
          description,
          blogPost: posts.slice(0, 20).map((p) => ({
            '@type': 'BlogPosting',
            headline: p.title,
            url: absoluteUrl(`/blog/${p.slug}`),
            datePublished: p.published_at,
          })),
        }}
      />
      <section className="section--ink blueprint page-hero" aria-labelledby="blog-title">
        <div className="container page-hero__inner">
          <Breadcrumbs items={[{ name: 'Blog', path: '/blog' }]} />
          <p className="eyebrow">Blog</p>
          <h1 id="blog-title" className="display">Notes on verifiable document AI</h1>
          <p className="lede">{description}</p>
        </div>
      </section>
      <section className="section">
        <div className="container">
          {posts.length === 0 ? (
            <p className="lede">No articles yet. Check back soon.</p>
          ) : (
            <div className="grid-3">
              {posts.map((post, i) => <PostCard key={post.id} post={post} eager={i < 3} />)}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
