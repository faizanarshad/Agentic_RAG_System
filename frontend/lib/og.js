// Shared layout for generated Open Graph / Twitter images (rendered by next/og at build time).
// Ticks are drawn as SVG: symbol glyphs are missing from the bundled font and would trigger a
// failing remote font download.
export const ogSize = { width: 1200, height: 630 };

function Tick({ size = 22, color = '#34d3bf' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <path d="m5 12.5 4.5 4.5L19 7.5" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function OgCard({ kicker, title, subtitle }) {
  const grid =
    'linear-gradient(rgba(148,170,214,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(148,170,214,0.12) 1px, transparent 1px)';
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '64px 72px',
        background: '#0b1220',
        backgroundImage: grid,
        backgroundSize: '64px 64px',
        color: '#e6ebf5',
        fontFamily: 'sans-serif',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 14,
            background: '#3552f2',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Tick size={34} color="#ffffff" />
        </div>
        <div style={{ display: 'flex', fontSize: 34, fontWeight: 700, letterSpacing: -1 }}>
          AIDocument<span style={{ color: '#8ea0ff' }}>Agent</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ display: 'flex', fontSize: 22, letterSpacing: 4, textTransform: 'uppercase', color: '#8ea0ff' }}>
          {kicker}
        </div>
        <div style={{ display: 'flex', fontSize: 64, fontWeight: 700, lineHeight: 1.05, letterSpacing: -2, maxWidth: 1000 }}>
          {title}
        </div>
        <div style={{ display: 'flex', fontSize: 28, color: '#a6b1c8', maxWidth: 980 }}>{subtitle}</div>
      </div>
      <div style={{ display: 'flex', gap: 28, fontSize: 22, color: '#34d3bf' }}>
        {['Located findings', 'Cited answers', 'Flagged gaps'].map((label) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tick />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
