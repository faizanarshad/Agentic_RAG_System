'use client';

import { useId, useRef, useState } from 'react';

const W = 800;
const H = 200;

const shortDate = (day) => new Date(`${day}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

// A "nice" axis maximum (1, 2, 2.5, 5, 10 × 10^n) so gridline labels are round numbers
function niceMax(value) {
  if (value <= 0) return 1;
  const exponent = Math.floor(Math.log10(value));
  const base = 10 ** exponent;
  const step = [1, 2, 2.5, 5, 10].find((s) => s * base >= value);
  return step * base;
}

/**
 * Single-series time series: 2px line, light area fill, recessive gridlines, crosshair + tooltip on
 * hover or arrow keys, and a table view for screen readers and exact values.
 */
export function TimeSeriesChart({ series, label, format = (v) => v.toLocaleString() }) {
  const [active, setActive] = useState(null);
  const plotRef = useRef(null);
  const gradientId = useId();
  const values = series.map((p) => p.value);
  const max = niceMax(Math.max(...values, 0));
  const x = (i) => (series.length === 1 ? W / 2 : (i / (series.length - 1)) * W);
  const y = (v) => H - (v / max) * H;
  const line = series.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ');
  const area = `${line} L${W},${H} L0,${H} Z`;
  const total = values.reduce((a, b) => a + b, 0);

  const onMove = (event) => {
    const rect = plotRef.current.getBoundingClientRect();
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    setActive(Math.round(ratio * (series.length - 1)));
  };

  const onKey = (event) => {
    if (event.key === 'ArrowRight') setActive((i) => Math.min((i ?? -1) + 1, series.length - 1));
    else if (event.key === 'ArrowLeft') setActive((i) => Math.max((i ?? series.length) - 1, 0));
    else if (event.key === 'Escape') setActive(null);
    else return;
    event.preventDefault();
  };

  const point = active !== null ? series[active] : null;
  const pctX = active !== null ? (x(active) / W) * 100 : 0;
  const pctY = point ? (y(point.value) / H) * 100 : 0;

  return (
    <figure className="ts-chart">
      <figcaption className="visually-hidden">{label}: total {format(total)} over {series.length} days</figcaption>
      <div className="ts-body">
        <div className="ts-yaxis" aria-hidden="true">
          <span>{format(max)}</span>
          <span>{format(max / 2)}</span>
          <span>0</span>
        </div>
        <div
          className="ts-plot"
          ref={plotRef}
          tabIndex={0}
          role="img"
          aria-label={`${label}. Use left and right arrow keys to read daily values.`}
          onMouseMove={onMove}
          onMouseLeave={() => setActive(null)}
          onKeyDown={onKey}
        >
          <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="var(--chart-series)" stopOpacity="0.22" />
                <stop offset="100%" stopColor="var(--chart-series)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {[0, 0.5, 1].map((t) => (
              <line key={t} x1="0" x2={W} y1={H * t} y2={H * t} className="ts-grid" vectorEffect="non-scaling-stroke" />
            ))}
            <path d={area} fill={`url(#${gradientId})`} />
            <path d={line} className="ts-line" vectorEffect="non-scaling-stroke" />
          </svg>
          {point && (
            <>
              <div className="ts-crosshair" style={{ left: `${pctX}%` }} />
              <div className="ts-dot" style={{ left: `${pctX}%`, top: `${pctY}%` }} />
              <div className={`ts-tooltip ${pctX > 70 ? 'left' : ''}`} style={{ left: `${pctX}%` }} role="status">
                <strong>{format(point.value)}</strong>
                <span>{shortDate(point.day)}</span>
              </div>
            </>
          )}
        </div>
      </div>
      <div className="ts-xaxis" aria-hidden="true">
        <span>{shortDate(series[0].day)}</span>
        <span>{shortDate(series[Math.floor(series.length / 2)].day)}</span>
        <span>{shortDate(series[series.length - 1].day)}</span>
      </div>
      <details className="ts-table">
        <summary>View as table</summary>
        <table className="legal-table">
          <thead><tr><th>Date</th><th>{label}</th></tr></thead>
          <tbody>
            {series.map((p) => (
              <tr key={p.day}><td>{p.day}</td><td>{format(p.value)}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

/** Horizontal bars with the value in text ink beside each bar. */
export function BarList({ items, formatLabel = (l) => l, formatValue = (v) => v.toLocaleString(), empty = 'No data yet' }) {
  if (!items || items.length === 0) return <p className="legal-empty-note">{empty}</p>;
  const max = Math.max(...items.map(([, v]) => v), 0) || 1;
  return (
    <div className="legal-bars">
      {items.map(([label, value]) => (
        <div className="legal-bar-row" key={label} title={`${formatLabel(label)}: ${formatValue(value)}`}>
          <span className="legal-bar-label">{formatLabel(label)}</span>
          <div className="legal-bar-track">
            <div className="legal-bar-fill" style={{ width: `${Math.max((value / max) * 100, 2)}%` }} />
          </div>
          <span className="legal-bar-value">{formatValue(value)}</span>
        </div>
      ))}
    </div>
  );
}

export function StatTile({ label, value, sub }) {
  return (
    <div className="legal-tile">
      <span className="legal-tile-label">{label}</span>
      <span className="legal-tile-value">{value}</span>
      {sub && <span className="legal-tile-sub">{sub}</span>}
    </div>
  );
}
