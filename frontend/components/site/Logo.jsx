// Brand mark: a document with a folded corner and a verification tick, on an ink tile.
export function LogoMark({ className = 'brand__mark' }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect width="32" height="32" rx="8" fill="#3552f2" />
      <path d="M10.5 7.5h7.2l4.8 4.8v11.2a1 1 0 0 1-1 1H10.5a1 1 0 0 1-1-1v-15a1 1 0 0 1 1-1Z" fill="none" stroke="#fff" strokeWidth="1.7" strokeLinejoin="round" />
      <path d="M17.5 7.7v4.8h4.8" fill="none" stroke="#fff" strokeWidth="1.7" strokeLinejoin="round" />
      <path d="m12.6 18.3 2.1 2.1 4.4-4.5" fill="none" stroke="#9fffe9" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Brand() {
  return (
    <>
      <LogoMark />
      <span className="brand__name">
        AIDocument<span>Agent</span>
      </span>
    </>
  );
}
