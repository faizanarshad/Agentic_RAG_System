import { ImageResponse } from 'next/og';
import { OgCard, ogSize } from '@/lib/og';

export const alt = 'AIDocumentAgent: AI agents that check the details in your documents';
export const size = ogSize;
export const contentType = 'image/png';

export default function Image() {
  return new ImageResponse(
    <OgCard
      kicker="Document intelligence, verified"
      title="AI agents that check the details in your documents"
      subtitle="Engineering drawing review, legal synthesis and clinical Q&A, with every result traceable."
    />,
    size
  );
}
