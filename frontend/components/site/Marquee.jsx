// Continuously scrolling strip (CSS only). The second copy is hidden from assistive technology,
// and with reduced motion the strip stays still and shows a single wrapped copy.
export default function Marquee({ label, items }) {
  const group = (hidden) => (
    <ul className="marquee__group" aria-hidden={hidden || undefined} role="list">
      {items.map((item) => (
        <li key={item} className="marquee__item">{item}</li>
      ))}
    </ul>
  );
  return (
    <div className="marquee" role="note" aria-label={label}>
      <span className="marquee__label">{label}</span>
      <div className="marquee__viewport">
        <div className="marquee__track">
          {group(false)}
          {group(true)}
        </div>
      </div>
    </div>
  );
}
