import Image from 'next/image';

// Product screenshot in a window frame with drafting-style registration marks and callouts.
// `image.file` is a static import, so width, height and the blur placeholder come from the build.
export default function ProductFrame({ image, label, light = false, eager = false, callouts = [], sizes }) {
  return (
    <figure className={`frame${light ? ' frame--light' : ''}`}>
      <div className="frame__chrome" aria-hidden="true">
        <i />
        <i />
        <i />
        <span>{label}</span>
      </div>
      <Image
        className="frame__image"
        src={image.file}
        alt={image.alt}
        sizes={sizes || '(min-width: 1024px) 620px, calc(100vw - 32px)'}
        loading={eager ? 'eager' : 'lazy'}
        fetchPriority={eager ? 'high' : 'auto'}
        placeholder={eager ? 'empty' : 'blur'} // a blur swap only helps below-the-fold images
      />
      {callouts.map((c) => (
        <p key={c.text} className={`callout callout--${c.position}`}>
          <span className={`callout__tag callout__tag--${c.tone}`}>{c.tag}</span>
          {c.text}
        </p>
      ))}
    </figure>
  );
}
