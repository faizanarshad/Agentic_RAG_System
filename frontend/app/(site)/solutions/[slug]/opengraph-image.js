import { ImageResponse } from 'next/og';
import { OgCard, ogSize } from '@/lib/og';
import { solutions } from '@/lib/content';

export const alt = 'AIDocumentAgent solution';
export const size = ogSize;
export const contentType = 'image/png';

export function generateStaticParams() {
  return Object.keys(solutions).map((slug) => ({ slug }));
}

export default async function Image({ params }) {
  const { slug } = await params;
  const solution = solutions[slug];
  return new ImageResponse(
    <OgCard kicker={solution.kicker} title={solution.metaTitle} subtitle={solution.lede} />,
    size
  );
}
